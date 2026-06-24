/*
 * IndCric WhatsApp group bot — Phase 2 client (the bridge the spike wasn't).
 *
 * The spike only PROVED send/read on a laptop and logged to the console. This
 * client actually connects the group to Django:
 *   1. DRAIN   GET  /api/bot/outbound/      → claim queued posts
 *      POST    → post each as text or a native Poll, then ack
 *      POST    /api/bot/outbound/ack/       → report sent/failed
 *   2. FORWARD group activity → POST /api/bot/inbound/ :
 *      - native poll votes        (kind='poll_vote')   ← the vote surface
 *      - 👍/👎 reactions on the bot's own message (kind='reaction')
 *      - typed text               (kind='text')         ← commands only; Django
 *        ignores conversational yes/no (allow_text_rsvp=False server-side)
 *      then apply any returned {type:'react'} action to the member's message.
 *
 * Local end-to-end: run Django on localhost + this bot; both on one machine, so
 * INDCRIC_BASE_URL=http://localhost:8000 needs no tunnel. Phase 3 swaps LocalAuth
 * for RemoteAuth + PM2 + a hosted VM. See .claude/features/whatsapp-group-bot.md.
 */
'use strict';

require('dotenv').config();
const { Client, LocalAuth, Poll } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const BASE = (process.env.INDCRIC_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const INBOUND_TOKEN = process.env.BOT_INBOUND_TOKEN || '';
const WEBHOOK_TOKEN = process.env.BOT_WEBHOOK_TOKEN || '';
const GROUP_JID = (process.env.WA_GROUP_JID || '').trim();
const POLL_MS = parseInt(process.env.POLL_INTERVAL_MS || '20000', 10);
// Reuse the spike's linked session by default (clientId 'indcric-spike') so you
// don't re-scan the QR for local testing. Override with WA_CLIENT_ID in prod.
const CLIENT_ID = process.env.WA_CLIENT_ID || 'indcric-spike';
// `node bot.js roster` (or ROSTER=1): one-shot — dump every group member as
// (lid, name) to /api/bot/roster/ for admin mapping, then exit. No drain loop.
const ROSTER_MODE = process.argv.includes('roster') || process.env.ROSTER === '1';

// Message ids WE posted, so we only forward votes/reactions on the bot's own
// messages (never arbitrary group activity). Map keeps the outbound row id too.
const ourMsgIds = new Set();
const ourPollMsgIds = new Set();

function toE164(waId) {
  const digits = (waId || '').split('@')[0].replace(/[^0-9]/g, '');
  return digits ? '+' + digits : '';
}

// Resolve a sender id to { phone, lid, name }. In Communities / privacy-on
// groups WhatsApp addresses people by '<lid>@lid' (opaque, NOT the phone), so we
// can't match on phone there — Django matches on the LID instead. We also grab
// the contact's display name so an unknown LID is mappable by a human admin.
async function resolveIdentity(waId) {
  const out = { phone: '', lid: '', name: '' };
  if (!waId) return out;
  if (waId.endsWith('@lid')) out.lid = waId.split('@')[0].replace(/[^0-9]/g, '');
  if (waId.endsWith('@c.us')) out.phone = toE164(waId);
  try {
    const c = await client.getContactById(waId);
    if (c) {
      if (c.number) out.phone = '+' + String(c.number).replace(/[^0-9]/g, '');
      out.name = c.pushname || c.name || c.shortName || '';
      const sid = c.id && c.id._serialized;
      if (!out.phone && sid && sid.endsWith('@c.us')) out.phone = toE164(sid);
    }
  } catch (e) {
    console.error('[RESOLVE] getContactById failed:', e.message);
  }
  if (!out.phone) out.phone = toE164(waId);   // fallback (likely LID digits)
  return out;
}

async function api(path, token, body) {
  const url = `${BASE}${path}?token=${encodeURIComponent(token)}`;
  const opts = body
    ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
    : { method: 'GET' };
  try {
    const resp = await fetch(url, opts);
    const text = await resp.text();
    let json = null;
    try { json = text ? JSON.parse(text) : null; } catch (_) {}
    if (!resp.ok) console.error(`[API] ${path} → HTTP ${resp.status} ${text.slice(0, 200)}`);
    return { ok: resp.ok, status: resp.status, json };
  } catch (e) {
    console.error(`[API] ${path} failed:`, e.message);
    return { ok: false, status: 0, json: null };
  }
}

const client = new Client({
  authStrategy: new LocalAuth({ clientId: CLIENT_ID }),
  // No webVersionCache — npm 1.34.7 is broken on WA Web 2.3000.x; this project
  // installs whatsapp-web.js from git main (see package.json), which fixes it.
  puppeteer: {
    headless: true,
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    protocolTimeout: 120000,
  },
});

client.on('qr', (qr) => {
  console.log('\n[QR] Scan with the bot SIM (Number B): WhatsApp → Linked Devices → Link a Device\n');
  qrcode.generate(qr, { small: true });
});
client.on('authenticated', () => console.log('[AUTH] authenticated'));
client.on('auth_failure', (m) => console.error('[AUTH_FAILURE]', m));
client.on('disconnected', (r) => console.warn('[DISCONNECTED]', r));

client.on('ready', async () => {
  console.log('\n===================== BOT READY =====================');
  try {
    const me = client.info && client.info.wid && client.info.wid._serialized;
    console.log('[ME] bot number:', toE164(me));
  } catch (_) {}
  if (!GROUP_JID) console.warn('[WARN] WA_GROUP_JID not set — drain will post nowhere.');
  if (!INBOUND_TOKEN || !WEBHOOK_TOKEN) console.warn('[WARN] BOT_INBOUND_TOKEN / BOT_WEBHOOK_TOKEN not set.');
  console.log(`[CFG] base=${BASE} group=${GROUP_JID || '(none)'} poll=${POLL_MS}ms`);
  console.log('=====================================================\n');
  if (ROSTER_MODE) { await dumpRoster(); return shutdown('roster-done'); }
  drainLoop();
});

// One-shot roster harvest: list the group's members and import their (lid, name)
// so an admin can map them in bulk (no waiting for each to vote).
async function dumpRoster() {
  if (!GROUP_JID) { console.error('[ROSTER] WA_GROUP_JID not set'); return; }
  let chat;
  try {
    chat = await client.getChatById(GROUP_JID);
  } catch (e) { console.error('[ROSTER] getChatById failed:', e.message); return; }

  // Participants can live on .participants or .groupMetadata.participants
  // depending on lib/sync state.
  let participants = (chat && chat.participants) || [];
  if (!participants.length && chat && chat.groupMetadata) {
    participants = chat.groupMetadata.participants || [];
  }
  console.log(`[ROSTER] chat="${chat && chat.name}" isGroup=${chat && chat.isGroup} participants=${participants.length}`);

  const members = [];
  for (const p of participants) {
    const pid = p.id && p.id._serialized;
    const id = await resolveIdentity(pid);   // @c.us → phone+name; @lid → lid+name
    members.push({ phone: id.phone, lid: id.lid, name: id.name });
    console.log(`[ROSTER] ${pid} phone=${id.phone} lid=${id.lid || '-'} name="${id.name}"`);
  }
  const { json } = await api('/api/bot/roster/', WEBHOOK_TOKEN, { members });
  console.log(`[ROSTER] sent ${members.length}; linked ${json && json.linked}; staged ${json && json.staged}`);
}

// ── 1. DRAIN: pull queued posts from Django and post them into the group ──
async function drainLoop() {
  for (;;) {
    await drainOnce();
    await new Promise((r) => setTimeout(r, POLL_MS));
  }
}

async function drainOnce() {
  if (!GROUP_JID) return;
  const { json } = await api('/api/bot/outbound/', WEBHOOK_TOKEN);
  const messages = (json && json.messages) || [];
  for (const m of messages) {
    try {
      let sent;
      if (m.kind === 'poll' && Array.isArray(m.poll_options) && m.poll_options.length) {
        sent = await client.sendMessage(GROUP_JID, new Poll(m.body, m.poll_options, { allowMultipleAnswers: false }));
        const id = sent.id && sent.id._serialized;
        if (id) { ourMsgIds.add(id); ourPollMsgIds.add(id); }
        console.log(`[POST] poll #${m.id} → ${id}`);
      } else {
        sent = await client.sendMessage(GROUP_JID, m.body);
        const id = sent.id && sent.id._serialized;
        if (id) ourMsgIds.add(id);
        console.log(`[POST] text #${m.id} → ${id}`);
      }
      await api('/api/bot/outbound/ack/', WEBHOOK_TOKEN, {
        id: m.id, status: 'sent', wa_message_id: (sent.id && sent.id._serialized) || '',
      });
    } catch (e) {
      console.error(`[POST] #${m.id} failed:`, e.message);
      await api('/api/bot/outbound/ack/', WEBHOOK_TOKEN, { id: m.id, status: 'failed', error: e.message.slice(0, 255) });
    }
  }
}

// ── 2. FORWARD: group activity → Django ──
async function forwardInbound(payload) {
  const { json } = await api('/api/bot/inbound/', INBOUND_TOKEN, payload);
  const actions = (json && json.actions) || [];
  for (const a of actions) {
    if (a.type === 'react' && a.message_id) {
      try {
        const msg = await client.getMessageById(a.message_id);
        if (msg) await msg.react(a.emoji);
      } catch (e) { console.error('[REACT] apply failed:', e.message); }
    }
  }
  return json;
}

client.on('vote_update', async (vote) => {
  const onMsg = vote.parentMessage && vote.parentMessage.id && vote.parentMessage.id._serialized;
  if (!onMsg) return;
  // Forward votes on ANY poll in the target group — not only ones we remember
  // posting. ourPollMsgIds is in-memory and forgotten on restart, but the bot is
  // the only thing posting IndCric polls and Django maps every poll vote to the
  // latest open poll, so a vote on an earlier poll still records correctly.
  const groupId = (GROUP_JID || '').split('@')[0];
  if (groupId && !onMsg.includes(groupId)) return;            // target group only
  const selected = (vote.selectedOptions || []).map((o) => o.name);
  const id = await resolveIdentity(vote.voter);
  console.log(`[VOTE] raw=${vote.voter} → phone=${id.phone} lid=${id.lid} name=${id.name} → ${JSON.stringify(selected)}`);
  forwardInbound({
    from: id.phone, lid: id.lid, author_name: id.name,
    // Timestamp makes each vote action a distinct event so a re-vote / change
    // always records (the Vote.update_or_create is the real idempotency).
    wa_message_id: `pollvote:${onMsg}:${vote.voter}:${selected.join('|')}:${Date.now()}`,
    kind: 'poll_vote', selected, chat: 'community',
  });
});

client.on('message_reaction', async (reaction) => {
  const onMsg = reaction.msgId && reaction.msgId._serialized;
  if (!onMsg || !ourMsgIds.has(onMsg)) return;                // only on OUR messages
  const id = await resolveIdentity(reaction.senderId);
  console.log(`[REACT-IN] raw=${reaction.senderId} → phone=${id.phone} lid=${id.lid} ${reaction.reaction || '(removed)'} on ${onMsg}`);
  forwardInbound({
    from: id.phone, lid: id.lid, author_name: id.name,
    wa_message_id: `react:${onMsg}:${reaction.senderId}:${reaction.reaction || 'x'}:${Date.now()}`,
    kind: 'reaction', emoji: reaction.reaction || '', chat: 'community',
  });
});

client.on('message', async (msg) => {
  if (!msg.from || !msg.from.endsWith('@g.us')) return;       // group only
  if (msg.from !== GROUP_JID) return;                          // target group only
  const body = (msg.body || '').trim();
  if (!body) return;
  const id = await resolveIdentity(msg.author || msg.from);
  // Typed text is forwarded as a command; Django ignores conversational yes/no.
  forwardInbound({
    from: id.phone, lid: id.lid, author_name: id.name,
    wa_message_id: msg.id && msg.id._serialized,
    kind: 'text', text: body, chat: 'community',
  });
});

async function shutdown(sig) {
  console.log(`\n[${sig}] shutting down…`);
  try { await client.destroy(); } catch (_) {}
  process.exit(0);
}
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

console.log('Starting IndCric group bot…');
client.initialize();
