# IndCric Bot — Phase 0 Spike

**Throwaway.** This proves whatsapp-web.js can post to + read from the club WhatsApp group, on a laptop, before we build anything real. Phase 1+ (Django queue, RemoteAuth, Oracle host) replaces all of this. Full plan: [.claude/features/whatsapp-group-bot.md](../.claude/features/whatsapp-group-bot.md).

## What it proves

1. **SEND** — bot posts a message into the group (`!ping` reply + optional startup hello).
2. **READ** — bot sees group replies and recovers the sender's phone number.
3. **REACT** — bot reacts ✅/❌ to a `YES`/`NO` message (the locked confirmation style).

## Prerequisites

- **Node.js 18+** installed (`node --version`).
- The **dedicated SIM** registered on the official WhatsApp app, added to a **private test group** (don't test in the real club group first).
- A **second phone** in that group to send test messages from.

## Run

```bash
cd bot
npm install            # first time — downloads Chromium, ~1 min
cp .env.example .env   # optional; you can fill WA_GROUP_JID after first run
node spike.js
```

1. A QR code prints. On the dedicated phone: **WhatsApp → Linked Devices → Link a Device → scan it.**
2. On `READY`, the console lists every group the account is in, with its JID:
   ```
   1234567890-1234567@g.us   "ICG Test Group"
   ```
   Copy the target JID into `.env` as `WA_GROUP_JID` (and set `SEND_HELLO=1` if you want a startup post), then re-run.
3. From the second phone, in that group, send:
   - `YES` or `NO` → bot reacts ✅/❌ and logs the sender's number.
   - `!ping` → bot replies `pong 🏓` (proves the text-send path).

## What success looks like

```
[GROUP MSG] group=...@g.us from=+32471000000 body="YES"
[REACT] ✅ for +32471000000 (choice=yes, session=latest)
        → in Phase 1 this would POST {from:"+32471000000", text:"YES"} to /api/bot/inbound/
```

If you see that, Phase 0 is done — the send/read/react loop works end-to-end. Tell me and we move to Phase 1 (the Django side).

## Notes / gotchas

- The session is cached in `.wwebjs_auth/` (gitignored) — re-runs won't need a re-scan until WhatsApp logs the device out.
- First `npm install` pulls a full Chromium via Puppeteer; on a slow link give it a few minutes.
- On Linux servers you'd set `CHROMIUM_PATH` to a system Chromium and keep `--no-sandbox`. On a laptop, leave it blank.
- This spike uses **LocalAuth** (disk). Production switches to **RemoteAuth** (Mongo Atlas) so the session survives server rebuilds — out of scope here.
