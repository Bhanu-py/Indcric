# IndCric Group Bot — Phase 3 Deployment

Take `bot/bot.js` from "runs on my laptop" to an always-on hosted service that
survives reboots **without re-scanning the QR**. Full design + rationale:
[../.claude/features/whatsapp-group-bot.md](../.claude/features/whatsapp-group-bot.md).

## What runs where
- **Django** stays on Render (always-on). It owns the queue + endpoints
  (`/api/bot/outbound/`, `/api/bot/outbound/ack/`, `/api/bot/inbound/`, `/api/bot/roster/`).
- **The bot** (`bot.js`) runs on a small always-on box, links **Number B** (the
  dedicated consumer SIM) via QR, and talks to Django over HTTPS.
- **Session persistence**: RemoteAuth → Mongo Atlas, so a restart/redeploy never
  needs a re-scan.

## 1. Django (Render) — enable the group bot
Set env vars on the Render service, then deploy (migrations run on deploy):
```
BOT_WEBHOOK_TOKEN=<random>           # outbound drain/ack + roster
BOT_INBOUND_TOKEN=<random, different># inbound (writes Votes — higher trust)
WHATSAPP_GROUP_BOT_ENABLED=1         # start auto-queuing group posts
```
`SITE_URL` is already set. Confirm `apps/notifications` migrations applied.

## 2. Mongo Atlas (free M0) — session store
1. Create a free M0 cluster (no card). Add a DB user + allow the host IP (or 0.0.0.0/0 for a spike).
2. Copy the connection string → that's `MONGODB_URI`.
- M0 auto-pauses after ~60 days of zero activity; the bot's 5-min session backups keep it warm.

## 3. The host (Oracle Cloud Always-Free A1, or fallback)
- **Oracle A1 ARM** (2 OCPU / 12 GB) runs headless Chromium comfortably. Caveat:
  card required for identity; A1 capacity is often "out of host capacity" in
  popular regions; idle reclaim risk. **Fallback:** Baileys on a 1 GB `e2-micro`
  (no Chromium) — different lib, separate spike needed.
- Install: Node 18+, git, and **system Chromium** (`sudo apt install chromium-browser`).
  Set `CHROMIUM_PATH=/usr/bin/chromium-browser` (don't rely on the bundled one on a server).

## 4. Deploy the bot
```bash
git clone https://github.com/Bhanu-py/Indcric.git && cd Indcric/bot
npm install                 # installs whatsapp-web.js from git main (the 2.3000.x fix)
cp .env.example .env        # then edit — see below
```
`bot/.env` (production):
```
INDCRIC_BASE_URL=https://indcric.onrender.com
BOT_INBOUND_TOKEN=<same as Render>
BOT_WEBHOOK_TOKEN=<same as Render>
WA_GROUP_JID=<the target sub-group @g.us>
WA_CLIENT_ID=indcric-bot          # distinct from the local 'indcric-spike'
MONGODB_URI=<Mongo Atlas string>  # enables RemoteAuth
CHROMIUM_PATH=/usr/bin/chromium-browser
POLL_INTERVAL_MS=25000
```

## 5. First link (one-time, interactive)
```bash
node bot.js                  # prints a QR
```
On the **Number B** phone: WhatsApp → Linked Devices → Link a Device → scan.
Wait for `[AUTH] remote session saved to Mongo` (~1 min after ready) — that confirms
persistence. `Ctrl+C`.

## 6. Supervise with PM2
```bash
npm i -g pm2
pm2 start ecosystem.config.js
pm2 save && pm2 startup      # run the printed command so it survives reboots
```
**Reboot test:** `sudo reboot` → after boot, `pm2 logs indcric-bot` should reach
`BOT READY` with **no QR** (RemoteAuth restored the session).

## 7. Onboard members
See GitHub issue #51. Once: `node bot.js roster` (sets `wa_name` by phone match),
then map any stragglers at `/admin/notifications/whatsappidentity/`.

## Operational safety
- **LOGOUT ≠ crash.** PM2 auto-restarts crashes. A `[AUTH] session was LOGGED OUT`
  line means WhatsApp invalidated the session — PM2 can't fix it; a human must
  re-scan with the SIM phone. Keep that phone charged + online (a linked device
  dies if the phone is offline > 14 days).
- **Dead-man's-switch** (recommended): an external cron (cron-job.org) that alerts
  you when the queue backs up or the bot goes quiet. A `/api/bot/heartbeat/`
  endpoint for this is a planned follow-up; until then, watch the `OutboundMessage`
  queue depth in `/admin/` (rows stuck `pending`/`claimed` = bot down).
- **Ban risk** (LOW at our volume): dedicated SIM you own; warm it ~1–2 weeks as a
  real phone; keep all activity in the one consenting group; vary wording; never
  cold-DM or scrape. A ban = re-link a spare SIM (the group is human-owned, so it survives).

## Troubleshooting
- **Stuck at inject / no events** → whatsapp-web.js vs WhatsApp Web `2.3000.x`. We
  install from git main; if it regresses, `rm -rf node_modules .wwebjs_auth && npm install`.
- **Votes not recording** → the voter isn't onboarded (no `wa_name`/`wa_lid`). Run
  the roster / map them. Check Django logs for `unknown identity`.
- **`fetch failed`** → wrong `INDCRIC_BASE_URL` or Django unreachable.
