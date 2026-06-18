# IndCric Bot — Phase 0 Spike

**Throwaway.** This proves whatsapp-web.js can post to + read from the club WhatsApp group, on a laptop, before we build anything real. Phase 1+ (Django queue, RemoteAuth, Oracle host) replaces all of this. Full plan: [.claude/features/whatsapp-group-bot.md](../.claude/features/whatsapp-group-bot.md).

## What it proves

1. **SEND** — bot posts into the group (text prompt, native poll, and `!ping` reply).
2. **READ** — bot recovers the sender's/voter's phone number from group activity.
3. **Three input mechanisms, compared head-to-head** — so we pick the one that
   actually fires reliably in a real group (this is the whole point of Phase 0):
   - **Typed** `YES`/`NO` → `[GROUP MSG]` (most robust, highest friction)
   - **Reactions** 👍/👎 on the bot's prompt → `[REACTION]` (low friction, but 👎
     isn't a one-tap default react; event reliability in groups is the question)
   - **Native WhatsApp Poll** Yes/No → `[POLL VOTE]` (lowest friction, native
     tally; but `vote_update` is the most fragile event on the unofficial lib)

Whichever of the three logs **reliably** is what we build Phase 1 on.

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
   Copy the target JID into `.env` as `WA_GROUP_JID`, set **`SEND_HELLO=1`** and
   **`SEND_POLL=1`** (to post both a reaction prompt and a native poll), re-run.
3. From the second phone, in that group, try **all three** inputs:
   - type `YES` / `NO`           → `[GROUP MSG]` then `[REACT]` ✅/❌
   - react 👍 / 👎 on the prompt  → `[REACTION]`
   - tap an option on the poll    → `[POLL VOTE]`
   - `!ping`                      → bot replies `pong 🏓` (proves text send)

## What success looks like

The goal is to see which of these three log **every time**, not just once:

```
[GROUP MSG]  from=+32471000000 body="YES"
[REACTION]   from=+32471000000 emoji=👍 on=...  (OUR rsvp message)
             → maps to YES for +32471000000; Phase 1 would update the Vote
[POLL VOTE]  from=+32471000000 selected=["Yes ✅"]  (OUR poll)
             → maps to YES for +32471000000; Phase 1 would update the Vote
```

**Report back which mechanism(s) fired reliably** (react each/poll-vote a few
times, change your mind, remove the reaction — does every change log?). That
decides the Phase 1 design. Then we build the Django side.

## Notes / gotchas

- The session is cached in `.wwebjs_auth/` (gitignored) — re-runs won't need a re-scan until WhatsApp logs the device out.
- First `npm install` pulls a full Chromium via Puppeteer; on a slow link give it a few minutes.
- On Linux servers you'd set `CHROMIUM_PATH` to a system Chromium and keep `--no-sandbox`. On a laptop, leave it blank.
- This spike uses **LocalAuth** (disk). Production switches to **RemoteAuth** (Mongo Atlas) so the session survives server rebuilds — out of scope here.
