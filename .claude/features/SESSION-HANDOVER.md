# Session Handover — WhatsApp Bot + Activity Feed

**Date:** 2026-06-19
**Branch model:** work on `stage` → PR/merge to `master` → Render auto-deploys `master`.
**Git state at handover:** all work committed + pushed; `stage` == `master` (in sync). Only untracked file is `static/icons/logo-mark1.png` (unrelated, leave it).

> This is the cross-machine pickup doc for everything done in this session. The two deep-dive docs it references are the source of truth for detail:
> - [whatsapp-bot.md](whatsapp-bot.md) — Cloud-API bot spec + cost pivot
> - [whatsapp-bot-HANDOVER.md](whatsapp-bot-HANDOVER.md) — Cloud-API shipped-state + Render env vars
> - [whatsapp-group-bot.md](whatsapp-group-bot.md) — the NEW group-resident bot spec (the active workstream)

## TL;DR — What Happened This Session

1. **Cloud-API resend hardening** — non-voters filter + 6h cooldown + BotEvent logging; "no creds" handled gracefully.
2. **Delivery diagnosis** — added the `statuses` webhook handler; found Meta error **131042 "Business eligibility payment issue"** = the Cloud-API broadcast DMs are *paid* utility conversations and need a billing threshold.
3. **Cost pivot** — stopped paid broadcasts; "Share to WhatsApp Group" button now generates a `wa.me` invite the admin pastes; members RSVP in the free 24h service window. `notify_poll_created` / `resend_poll_invite` / `send_session_reminders` kept as disabled escape hatches.
4. **STATUS command** — DM `STATUS`/`POLL`/`WHO` → current poll counts + voter lists.
5. **Activity feed polish** — red ❌ for "no" RSVPs (green ✅ stays for yes); reaction palette 🎉 → 🔥.
6. **NEW workstream: group-resident bot** — designed via a multi-agent research+critique pass. A Node `whatsapp-web.js` bot will live IN the WhatsApp Community group, auto-post club updates, and read RSVPs. Phase 0 spike written ([bot/](../../bot/)).
7. **Two hard constraints discovered** (see below) that shape the group-bot build.

## Two Constraints That Drive Everything

1. **Cloud API cannot post to / join groups.** "This business can't be added to groups" — a Meta restriction with no workaround. This is the entire reason the group bot exists.
2. **A number is on Cloud API XOR the consumer app — never both.** So we use **two numbers**:
   - **Number A** = existing "ICG" Cloud-API number → 1:1 DM features only.
   - **Number B** = a NEW dedicated SIM on the **plain WhatsApp app** (never the Cloud API) → the group bot, linked via QR.

## 🔴 THE IMMEDIATE NEXT ACTION

**Validate the Phase 0 spike** — answer empirically: which vote-input mechanism fires reliably in a real WhatsApp group? (typed `YES`/`NO` vs reactions 👍/👎 vs native Yes/No Poll). This is the only thing blocking the Phase 1 (Django) build.

Two ways to do it:
- **Quick tech check (today, no new SIM):** scan the spike with ANY spare consumer WhatsApp number into a throwaway test group, react + poll-vote a few times, see which `[REACTION]` / `[POLL VOTE]` / `[GROUP MSG]` lines log reliably. No club data touched.
- **Real setup:** register **Number B** (new SIM) on plain WhatsApp, warm it up ~1–2 weeks, then run the spike.

### Running the spike on a new machine
```bash
cd bot
npm install            # needs Node 18+; first run downloads Chromium (~1 min)
cp .env.example .env   # set WA_GROUP_JID after the first READY log; SEND_HELLO=1 SEND_POLL=1
node spike.js          # scan the QR with Number B (or a spare number) via Linked Devices
```
- `bot/.wwebjs_auth/` (the logged-in session) is **per-machine + gitignored** → you re-scan the QR on each new computer. Expected.
- `bot/package.json` is force-added (root `.gitignore` blanket-ignores `*.json`) — it IS in the repo.
- Full instructions + "what success looks like": [bot/README.md](../../bot/README.md).

**Report back:** does every reaction change log a `[REACTION]`? Does the poll log `[POLL VOTE]` at all? That decides Phase 1.

## New-Machine Setup (Django app)

```bash
git clone https://github.com/Bhanu-py/Indcric.git c:\GCC\Indcric
cd c:\GCC\Indcric
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d            # local Postgres
python manage.py migrate
python manage.py runserver
git checkout stage              # work happens on stage
```
Local `.env` minimum: `DEBUG=True`, the `db_*` vars, `BOT_WEBHOOK_TOKEN`. WhatsApp Cloud-API vars are NOT needed locally (can't test Meta against localhost). Full env-var table (all 9 Cloud-API vars + `WHATSAPP_BOT_NUMBER`) is in [whatsapp-bot-HANDOVER.md](whatsapp-bot-HANDOVER.md).

## State of Each Workstream

| Workstream | Status | Where |
|---|---|---|
| Cloud-API resend / STATUS / group-share | ✅ Shipped on master | `apps/notifications/{services,views}.py`, `apps/sessions/views.py` |
| Activity feed red-X + 🔥 | ✅ Shipped on master | `apps/notifications/{activity,views}.py`, `_activity_row.html` |
| Group-bot spec | ✅ Designed, locked decisions | [whatsapp-group-bot.md](whatsapp-group-bot.md) |
| Group-bot Phase 0 spike | ✅ Written, ⏳ NOT YET RUN by user | [bot/](../../bot/) |
| Group-bot Phase 1 (Django) | ⛔ Blocked on Phase 0 result | — |

## Group-Bot Build Plan (after Phase 0)

From [whatsapp-group-bot.md](whatsapp-group-bot.md):
- **Phase 1 (Django):** `OutboundMessage` queue model; `/api/bot/inbound/`; refactor `_process_message` → `dispatch_inbound` (write a characterization test first); `clean_phone` normalization; split `BOT_INBOUND_TOKEN`.
- **Phase 2 (post):** `outbound_drain`/`ack` endpoints (claimed-status + reclaim window to avoid dup posts); `build_group_rsvp_text` composer (do NOT reuse `build_group_invite_text` — it emits wa.me deep-links, wrong for in-group); enqueue from signals.
- **Phase 3 (prod):** Oracle Cloud A1 VM (free), PM2, RemoteAuth+Mongo Atlas (zero re-scan), dead-man's-switch heartbeat + alerting, single reminder.

## Decisions

**Locked:** two-number architecture · accept Oracle datacenter IP · emoji-react confirmations (RSVP = reaction, not text) · Phase 0 first · Node-pulls-queue (not Django-push) · whatsapp-web.js over Baileys.

**Note:** Django is on an **always-on (paid) Render** server, NOT free tier — so it doesn't sleep. (Earlier design drafts assumed sleep; that's corrected in the spec.)

**Still open** (revisit at the phase that needs them): vote-input mechanism (Phase 0 decides) · session store (Mongo M0 recommended) · donation post gate · reminder timing · alerting channel.

## Gotchas to Remember

- `WHATSAPP_PHONE_NUMBER_ID` (Meta's numeric ID) ≠ `WHATSAPP_BOT_NUMBER` (the wa.me E.164 number). Different things, both needed.
- Meta `statuses` callbacks tell you real delivery outcomes — a "success" in send logs only means Meta *accepted* it. Check `BotEvent` rows `action='wa_status'`, `payload.errors[0].code`.
- 👎 is NOT a one-tap WhatsApp reaction (only 👍 is) — that's why the native Poll is a candidate over 👍/👎.
- Number B must NEVER be registered on the Cloud API or it hits the same group wall.
