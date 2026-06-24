/*
 * IndCric WhatsApp bot — PHASE 0 SPIKE (throwaway).
 *
 * Goal: prove the two things the whole group-bot plan rests on, on a laptop,
 * before we touch Django or provision a server:
 *   (1) SEND   — the bot can post a message into the club group.
 *   (2) READ   — the bot sees members' replies in the group, with their number.
 *   (3) REACT  — the chosen confirmation style (emoji-react ✅/❌ to an RSVP).
 *
 * This is NOT production code. It uses LocalAuth (session on local disk), no
 * Django, no queue, no RemoteAuth, no error handling beyond logging. Phase 1+
 * replaces all of it. See .claude/features/whatsapp-group-bot.md.
 *
 * Run:  npm install  &&  node spike.js
 * Then: scan the QR with the DEDICATED SIM's WhatsApp (Linked Devices).
 *
 * What to watch for in the console:
 *   - "READY" then a list of your groups with their JIDs  → copy the target
 *     group's JID into WA_GROUP_JID (.env) to enable the startup hello + !ping.
 *   - Send "YES" / "NO" in that group from another phone → the bot reacts ✅/❌
 *     and logs the author's number. That's the full read+react loop.
 *   - Send "!ping" in the group → the bot replies with a text message (proves
 *     the send path beyond the startup hello).
 */

'use strict';

require('dotenv').config();
const { Client, LocalAuth, Poll } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// Optional: set WA_GROUP_JID in .env once you've captured it from the READY log.
const TARGET_GROUP_JID = (process.env.WA_GROUP_JID || '').trim();
// Set SEND_HELLO=1 to post a one-line text RSVP prompt into the target group on
// startup. Members can REACT to it (👍 yes / 👎 no) or type YES/NO.
const SEND_HELLO = process.env.SEND_HELLO === '1';
// Set SEND_POLL=1 to post a native WhatsApp Poll (Yes/No) into the target group
// on startup. Members tap an option; we listen for vote_update.
const SEND_POLL = process.env.SEND_POLL === '1';

// We remember the ids of the messages we post so we can tell whether an incoming
// reaction / vote is against OUR RSVP message vs some other message.
let lastRsvpMsgId = null;   // the text prompt people react to
let lastPollMsgId = null;   // the native poll people vote on

// Mirror of the Django RSVP_PATTERN so the spike behaves like the real parser.
// Matches: "yes", "NO", "y", "n", "✅", "❌", "1", "2", optionally followed by
// a session id ("YES 42", "no #7"). Case-insensitive.
const RSVP_PATTERN = /^\s*(yes|no|y|n|✅|❌|1|2)\s*(?:[#\s]*(\d+))?\s*$/i;

function classifyRsvp(text) {
  const m = RSVP_PATTERN.exec(text || '');
  if (!m) return null;
  const token = m[1].toLowerCase();
  const choice = ['yes', 'y', '✅', '1'].includes(token) ? 'yes' : 'no';
  const sessionId = m[2] ? parseInt(m[2], 10) : null;
  return { choice, sessionId };
}

// Strip a WhatsApp "<number>@c.us" id down to E.164 "+<number>" — the format
// Django's User.phone uses. Real impl lives in Django; this is just to prove the
// number is recoverable from a group message.
function toE164(waId) {
  const digits = (waId || '').split('@')[0].replace(/[^0-9]/g, '');
  return digits ? '+' + digits : '(unknown)';
}

const client = new Client({
  authStrategy: new LocalAuth({ clientId: 'indcric-spike' }),
  puppeteer: {
    headless: true,
    // On a server you'd point this at a system Chromium. On a laptop the bundled
    // one is fine, so leave CHROMIUM_PATH unset locally.
    executablePath: process.env.CHROMIUM_PATH || undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    // Give the WhatsApp Web inject more headroom on a cold/slow start so we don't
    // hit "Runtime.callFunctionOn timed out" before READY.
    protocolTimeout: 120000,
  },
});

client.on('qr', (qr) => {
  console.log('\n[QR] Scan this with the dedicated SIM: WhatsApp → Linked Devices → Link a Device\n');
  qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => console.log('[AUTH] authenticated — session will be cached in .wwebjs_auth/'));
client.on('auth_failure', (m) => console.error('[AUTH_FAILURE]', m));
client.on('change_state', (s) => console.log('[STATE]', s));
client.on('disconnected', (reason) => console.warn('[DISCONNECTED]', reason));

client.on('ready', async () => {
  console.log('\n========================= READY =========================');
  try {
    const chats = await client.getChats();
    const groups = chats.filter((c) => c.id && c.id.server === 'g.us');
    if (!groups.length) {
      console.log('No groups found. Add the bot number to your club group, then re-run.');
    } else {
      console.log('Groups this account is in (copy the target JID into WA_GROUP_JID):\n');
      for (const g of groups) {
        console.log(`  ${g.id._serialized}   "${g.name}"`);
      }
    }
  } catch (e) {
    console.error('[READY] getChats failed:', e.message);
  }
  try {
    const me = client.info && client.info.wid && client.info.wid._serialized;
    console.log('[ME] bot is logged in as:', toE164(me), '— do NOT send test messages from this number.');
  } catch (_) {}
  console.log('========================================================\n');

  if (TARGET_GROUP_JID && SEND_HELLO) {
    try {
      const sent = await client.sendMessage(
        TARGET_GROUP_JID,
        '🏏 IndCric RSVP test — react 👍 for YES / 👎 for NO on THIS message (or type YES/NO).'
      );
      lastRsvpMsgId = sent.id && sent.id._serialized;
      console.log('[SEND] text RSVP prompt posted; msgId=', lastRsvpMsgId);
    } catch (e) {
      console.error('[SEND] text RSVP prompt failed:', e.message);
    }
  }

  if (TARGET_GROUP_JID && SEND_POLL) {
    try {
      // Native WhatsApp Poll. Single-answer so it behaves like yes/no.
      const poll = new Poll('Are you in for the session?', ['Yes ✅', 'No ❌'], {
        allowMultipleAnswers: false,
      });
      const sent = await client.sendMessage(TARGET_GROUP_JID, poll);
      lastPollMsgId = sent.id && sent.id._serialized;
      console.log('[SEND] native poll posted; msgId=', lastPollMsgId);
    } catch (e) {
      console.error('[SEND] native poll failed (vote_update may be unsupported on this version):', e.message);
    }
  }

  if (!SEND_HELLO && !SEND_POLL) {
    console.log('[SEND] nothing posted (set WA_GROUP_JID + SEND_HELLO=1 and/or SEND_POLL=1).');
  }
  console.log('\nNow, from another phone in the group, try ALL THREE inputs:');
  console.log('  • type YES / NO            → [GROUP MSG] + [REACT]');
  console.log('  • react 👍 / 👎 to the prompt → [REACTION]');
  console.log('  • tap an option on the poll  → [POLL VOTE]');
  console.log('Whichever of these logs reliably is the one we build on.\n');
});

client.on('message', async (msg) => {
  // Only care about group messages for this spike.
  const isGroup = msg.from && msg.from.endsWith('@g.us');
  if (!isGroup) return;

  // In a group, msg.author is the sender's "<number>@c.us"; msg.from is the group.
  const author = msg.author || msg.from;
  const phone = toE164(author);
  const body = (msg.body || '').trim();
  console.log(`[GROUP MSG] group=${msg.from} from=${phone} body=${JSON.stringify(body)}`);

  // !ping → prove the text-send path (beyond startup hello).
  if (body.toLowerCase() === '!ping') {
    try {
      await msg.reply('pong 🏓 — spike is reading the group.');
      console.log('[REPLY] pong sent');
    } catch (e) {
      console.error('[REPLY] pong failed:', e.message);
    }
    return;
  }

  // RSVP → emoji-react (the locked confirmation style). No text reply.
  const rsvp = classifyRsvp(body);
  if (rsvp) {
    const emoji = rsvp.choice === 'yes' ? '✅' : '❌';
    try {
      await msg.react(emoji);
      console.log(`[REACT] ${emoji} for ${phone} (choice=${rsvp.choice}, session=${rsvp.sessionId ?? 'latest'})`);
      console.log(`        → in Phase 1 this would POST {from:"${phone}", text:${JSON.stringify(body)}} to /api/bot/inbound/`);
    } catch (e) {
      console.error('[REACT] failed:', e.message);
    }
    return;
  }

  // Anything else: in production a command (HELP/STATUS/…) would get a text reply.
  console.log('        (not an RSVP — a command/other; Phase 1 routes this to the dispatcher)');
});

// DIAGNOSTIC (Phase 0 debug): fires for EVERY group message incl. the bot's own.
// If !ping shows up here with fromMe=true but NOT under [GROUP MSG], you're
// sending from the bot's own number — test from a DIFFERENT person's WhatsApp.
// If NOTHING logs here either, the bot isn't receiving the group at all.
client.on('message_create', (msg) => {
  const isGroup = msg.from && msg.from.endsWith('@g.us');
  if (!isGroup) return;
  const author = msg.author || msg.from;
  console.log(`[MSG_CREATE] author=${toE164(author)} fromMe=${msg.fromMe} body=${JSON.stringify((msg.body || '').trim())}`);
});

// ── INPUT MODE 2: reactions (👍 yes / 👎 no on our RSVP message) ──
// Fires when someone adds, changes, or removes a reaction. `reaction` is '' on
// removal. This is the event we're testing for reliability in a group.
client.on('message_reaction', (reaction) => {
  try {
    const phone = toE164(reaction.senderId);
    const emoji = reaction.reaction || '(removed)';
    const onMsg = reaction.msgId && reaction.msgId._serialized;
    const mine = lastRsvpMsgId && onMsg === lastRsvpMsgId ? ' (OUR rsvp message)' : '';
    console.log(`[REACTION] from=${phone} emoji=${emoji} on=${onMsg}${mine}`);

    let choice = null;
    if (reaction.reaction === '👍') choice = 'yes';
    else if (reaction.reaction === '👎') choice = 'no';
    else if (reaction.reaction === '') choice = 'withdraw';

    if (choice && mine) {
      console.log(`        → maps to ${choice.toUpperCase()} for ${phone}; Phase 1 would update the Vote`);
    } else if (choice) {
      console.log(`        → ${choice} reaction, but not on our rsvp message — ignored`);
    } else {
      console.log('        → not a 👍/👎 reaction — ignored');
    }
  } catch (e) {
    console.error('[REACTION] handler error:', e.message);
  }
});

// ── INPUT MODE 3: native WhatsApp Poll votes ──
// Fires when someone selects/changes a poll option. selectedOptions is the
// current selection (empty when they deselect). vote_update is the most fragile
// of the three on the unofficial lib — if this never logs, the poll path is out.
client.on('vote_update', (vote) => {
  try {
    const phone = toE164(vote.voter);
    const selected = (vote.selectedOptions || []).map((o) => o.name);
    const onMsg = vote.parentMessage && vote.parentMessage.id && vote.parentMessage.id._serialized;
    const mine = lastPollMsgId && onMsg === lastPollMsgId ? ' (OUR poll)' : '';
    console.log(`[POLL VOTE] from=${phone} selected=${JSON.stringify(selected)} on=${onMsg}${mine}`);
    const choice = selected.length === 0 ? 'withdraw'
      : selected[0].toLowerCase().startsWith('yes') ? 'yes' : 'no';
    console.log(`        → maps to ${choice.toUpperCase()} for ${phone}; Phase 1 would update the Vote`);
  } catch (e) {
    console.error('[POLL VOTE] handler error:', e.message);
  }
});

// Graceful shutdown so Chrome flushes its session before exit.
async function shutdown(sig) {
  console.log(`\n[${sig}] shutting down…`);
  try { await client.destroy(); } catch (_) {}
  process.exit(0);
}
process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

console.log('Initializing whatsapp-web.js spike… (first run downloads Chromium, can take a minute)');
client.initialize();
