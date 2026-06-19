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

## 🟢 PHASE 0 PASSED 2026-06-19 — group-bot unblocked, build Phase 1 next

Ran on a fresh machine. After fixing a real upstream bug, **SEND + READ both work end-to-end.**
- ✅ Number B (`+32465110367`) linked via QR; bot posted the text prompt **and** a native poll into the "App development" test group.
- ✅ With multiple real members testing: typed `YES`/`NO` (rock solid), native poll `vote_update` (reliable), reactions (fire, with caveats below).
- **The blocker + fix:** npm `whatsapp-web.js@1.34.7` can't read events on live WhatsApp Web `2.3000.x` (events dead, `Client.inject` crashes — bugs [#127084](https://github.com/pedroslopez/whatsapp-web.js/issues/127084), [#5765](https://github.com/wwebjs/whatsapp-web.js/issues/5765)). **Fix:** NO `webVersionCache`; delete `node_modules`/`.wwebjs_auth`/`.wwebjs_cache`; `npm install github:pedroslopez/whatsapp-web.js#main` (commit `2dc9466`, still labels itself 1.34.7).
- **Two Phase-1 must-fixes the spike found:** (1) normalize emoji — skin-tone modifiers (`👍🏾`) broke the bare `=== '👍'` match and dropped a valid vote; (2) ignore reactions/messages from the bot's own number (it sees its own ✅/❌ confirmations echoed).
- **Recommended input:** native Poll primary + typed `YES`/`NO` fallback; reactions secondary.

## 🟢 PHASE 1 (Django) BUILT 2026-06-19 — 31/31 tests green (uncommitted on `stage`)

Receive-side Django is done and tested; the Node client is the only remaining piece.
- **Files:** `OutboundMessage` model + migration `0005_outboundmessage.py` + admin; `dispatch_inbound` + optional `reply` sink on every handler in `views.py` (Meta path unchanged — defaults to DM); `_check_bot_token` + `BOT_INBOUND_TOKEN`; new `views_bot.py` with `POST /api/bot/inbound/`; `clean_phone` strips internal separators in `accounts/forms.py`.
- **Endpoint behaviour:** auth via `?token=$BOT_INBOUND_TOKEN`; `kind=text|reaction|poll_vote`; emoji-normalized (`👍🏾`==`👍`); ignores the bot's own number; RSVP → records `Vote` + returns `{type:'react'}` action; commands → enqueue `OutboundMessage`; idempotent.
- **Also fixed:** `_log_inbound` now uses a `transaction.atomic()` savepoint so a deduped insert doesn't break the surrounding transaction (Postgres).
- **Run tests:** `python manage.py test apps.notifications --keepdb --noinput` (always pass `--noinput`, or a leftover `test_indcric_db` makes it hang on a stdin prompt).
- **Behaviour locked 2026-06-19:** group votes come from the **native poll + 👍/👎 reactions on the bot's message ONLY** — typed `yes`/`no` in the group is NOT a vote (false-positive from normal chat). `dispatch_inbound` gained `allow_text_rsvp` / `reply_unknown`; the inbound endpoint sets `allow_text_rsvp=True` only for `kind=reaction|poll_vote`, and `reply_unknown=False` for all group text. DM path unchanged. (33/33 tests green.)
- **Next action:** **Phase 2** — Node client (`bot/`) that forwards group activity to `/api/bot/inbound/` (only reactions on the bot's RSVP message + poll votes as votes; text only for commands) and performs the returned `react` action, plus `outbound_drain`/`ack` so it posts queued `OutboundMessage` rows. See [whatsapp-group-bot.md](whatsapp-group-bot.md) Phase 2.

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
| Group-bot Phase 0 spike | ✅ PASSED 2026-06-19 — SEND + READ work (git-main fix) | [bot/](../../bot/) |
| Group-bot Phase 1 (Django) | 🔜 Unblocked — ready to build | [whatsapp-group-bot.md](whatsapp-group-bot.md) |

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
