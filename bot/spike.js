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
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

// Optional: set WA_GROUP_JID in .env once you've captured it from the READY log.
const TARGET_GROUP_JID = (process.env.WA_GROUP_JID || '').trim();
// Set SEND_HELLO=1 to post a one-line "spike is live" into the target group on
// startup. Off by default so re-runs don't spam the group.
const SEND_HELLO = process.env.SEND_HELLO === '1';

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
  console.log('========================================================\n');

  if (TARGET_GROUP_JID && SEND_HELLO) {
    try {
      await client.sendMessage(TARGET_GROUP_JID, '🏏 IndCric bot spike is live — reply YES or NO to test.');
      console.log('[SEND] startup hello posted to', TARGET_GROUP_JID);
    } catch (e) {
      console.error('[SEND] startup hello failed:', e.message);
    }
  } else {
    console.log('[SEND] startup hello skipped (set WA_GROUP_JID and SEND_HELLO=1 to enable).');
  }
  console.log('Now send YES / NO / !ping in the group from another phone…\n');
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
