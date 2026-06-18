# WhatsApp Bot — Handover (Cross-Machine)

**Last updated:** 2026-06-18
**Status:** Tier 1 shipped on Meta Cloud API + free group-share flow. Live on Render. POC stable.
**Resume on:** Any computer, fresh clone — pick up from the "What's Next" list below.

> Read [whatsapp-bot.md](whatsapp-bot.md) for the full architecture and the cost-pivot rationale. This file is the cross-machine pickup checklist + current state snapshot.

## Where We Are

**Architecture:** Meta WhatsApp Cloud API (not `whatsapp-web.js`). Admin pastes a formatted invite into the WhatsApp Community group from their own phone; members tap `wa.me/<bot>?text=YES%20<session_id>` deep links to RSVP. All bot replies happen in the free 24h service window the user's tap opens — zero paid utility conversations at default volume.

**Shipped on master:**
- `User.phone` field (E.164, indexed, unique-when-set)
- `BotEvent` model in `apps/notifications/models.py` — audit log keyed on `wa_message_id`
- Cloud API webhook at `/api/bot/whatsapp/` with `X-Hub-Signature-256` verification
- `statuses` delivery-callback handler — Meta failure codes land in `BotEvent.payload.errors[0].code`
- Group-share flow: `build_group_invite_text` + `build_group_share_url` in `apps/notifications/services.py`; "Share to WhatsApp Group" link in the session-detail 3-dot menu
- Inbound commands (all free, service-window):
  - `YES` / `NO` / `YES <session_id>` / `NO <session_id>` — votes (case-insensitive, tolerates `No 3`, `YES 17`, `y #5`, etc.)
  - `BALANCE` / `BAL` / `WALLET` — wallet sum + outstanding sessions
  - `STATUS` / `POLL` / `WHO` / `COUNT` — open poll counts + voter lists
  - `HELP` / `?` — command list
- Bot replies: confirmation on successful RSVP ("Got it — recorded YES for …"), "I don't recognise this number" for unknown phones, "I didn't understand 'X'" with echo for unparseable text
- Activity feed RSVPs differentiate: green check for `yes`, red X for `no` (in `apps/notifications/activity.py` + `_decorate` in views; body-text inspection picks the no-style)

**Disabled but kept as escape hatches** (still in `services.py`, no UI surface):
- `notify_poll_created` — broadcast template DM
- `resend_poll_invite` — non-voters resend with cooldown
- `send_session_reminders` — 24h / morning / 2h reminders (also gated by `WHATSAPP_REMINDER_TEMPLATE` env var)

**Never built (and explicitly out of scope for now):**
- `WhatsAppGroup` model — not needed; admin manually picks the group when sharing
- `whatsapp-web.js` Node bot — not needed unless we want bot-posts-in-group (ban risk + infra cost)

## Render — Environment Variables (all in env, not in repo)

| Var | Purpose | Example / format |
|---|---|---|
| `WHATSAPP_PHONE_NUMBER_ID` | Meta's internal phone ID, NOT the actual number | `1234567890...` (numeric ID) |
| `WHATSAPP_ACCESS_TOKEN` | Long-lived Meta access token | `EAAxxxxxxxxxxxxx...` |
| `WHATSAPP_VERIFY_TOKEN` | Webhook subscription verification token | any random string |
| `WHATSAPP_APP_SECRET` | Verifies `X-Hub-Signature-256` on inbound webhooks | from Meta app dashboard |
| `WHATSAPP_RSVP_TEMPLATE` | Approved template name | `session_rsvp_temp` (default) |
| `WHATSAPP_TEMPLATE_LANGUAGE` | Locale code | `en_GB` (default) |
| `WHATSAPP_REMINDER_TEMPLATE` | If empty, reminders no-op | leave **empty** to keep reminders off |
| `WHATSAPP_BOT_NUMBER` | Bot's E.164 number for `wa.me/` deep links | `+32XXXXXXXXX` — digits stripped automatically |
| `BOT_WEBHOOK_TOKEN` | Auth for `/api/bot/run-reminders/` cron URL | any random string |

If `WHATSAPP_BOT_NUMBER` is empty, the "Share to WhatsApp Group" link is hidden in the template (sane fallback). If `WHATSAPP_PHONE_NUMBER_ID` or `WHATSAPP_ACCESS_TOKEN` is empty, the `resend_poll_invite` escape hatch bails early with a clear flash; everything else still works.

## New-Machine Setup

```powershell
git clone https://github.com/Bhanu-py/Indcric.git c:\GCC\Indcric
cd c:\GCC\Indcric
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
docker-compose up -d                  # local Postgres
python manage.py migrate
python manage.py runserver
```

**Local `.env`** — WhatsApp vars are typically NOT needed locally (the bot can't be tested against Meta without exposing your localhost via ngrok anyway; see "Testing the bot" below). At minimum you want:

```
DEBUG=True
db_hostname=localhost
db_databasename=indcric_db
db_username=indcric_user
db_password=indcric_password
BOT_WEBHOOK_TOKEN=<any-random-string>
```

## Testing the Bot

**Local-only flow checks** (no Meta involvement):
- Hit `/session/<id>/` in the browser to verify the "Share to WhatsApp Group" link appears (only when `WHATSAPP_BOT_NUMBER` is set in your local env)
- Open the link → confirms the `wa.me/?text=…` URL has the correct invite text encoded
- Activity feed: vote yes/no on a poll, refresh `/notifications/`, verify red X for no / green check for yes

**End-to-end with real WhatsApp** — only works through Render (Meta only knows that URL). To debug inbound on local:

1. `ngrok http 8000` (or cloudflared tunnel) → get a public HTTPS URL
2. Meta dev console → WhatsApp → Webhook → temporarily set URL to the ngrok one
3. Reload the bot — Meta will re-verify with `WHATSAPP_VERIFY_TOKEN`
4. Test → inbound hits your local Django; logs show RSVP_PATTERN matches and replies
5. **Switch the webhook URL back to Render** when done, or the prod bot stops working

## Files to Read First (in this order)

1. [whatsapp-bot.md](whatsapp-bot.md) — full spec + cost pivot rationale
2. [apps/notifications/services.py](../../apps/notifications/services.py) — `send_template_message`, `send_text_message`, `build_group_invite_text`, `build_group_share_url`, plus the still-disabled `notify_poll_created` / `resend_poll_invite` / `send_session_reminders`
3. [apps/notifications/views.py](../../apps/notifications/views.py) — webhook entry point, signature verification, `_process_message` dispatcher, all handlers
4. [apps/notifications/models.py](../../apps/notifications/models.py) — `BotEvent`, `ActivityEvent`, `Reaction`
5. [apps/sessions/views.py](../../apps/sessions/views.py) — session detail view (where `whatsapp_share_url` is built and passed to the template) and the still-callable `resend_poll_notifications_view`
6. [cric/templates/cric/pages/session_detail.html](../../cric/templates/cric/pages/session_detail.html) — the 3-dot menu with the share link
7. [apps/notifications/tests.py](../../apps/notifications/tests.py) — 25 tests cover RSVP emit, dedup, status reply formatting, signature verification

## What's Next (Priority Order)

These are the post-pivot priorities — none are blocking, all are nice-to-have improvements:

1. **Phone-onboarding deep-link** (~15 min) — when bot replies "I don't recognise this number", include a direct link to the profile-edit page so users can self-register their WhatsApp number.
2. **`STATUS <session_id>` + `MYVOTE`** (~20 min) — extend `RSVP_PATTERN` and dispatcher to handle these; cheap UX wins.
3. **Free reminder system** (~1 hour) — use the `BotEvent` inbound log to find users with an open 24h service window, send them a free reminder text. Doesn't cover everyone but covers the engaged subset for €0.
4. **Phone validation on save** — the inbound webhook normalises to `+E.164`, but `User.phone` field accepts whatever the form submits. Add a `clean_phone` that strips spaces/dashes and enforces the `+` prefix, otherwise wa.me deep links won't find the user.
5. **`BotEvent` admin filter** — currently you can browse at `/admin/notifications/botevent/` but there's no filter by `action` or `direction`. A small `list_filter` addition makes debugging much faster.

## Things to NOT Forget

- `BOT_WEBHOOK_TOKEN` is for the cron-callable `/api/bot/run-reminders/` URL — separate from Meta credentials.
- `WHATSAPP_PHONE_NUMBER_ID` (Meta's ID, numeric only) ≠ `WHATSAPP_BOT_NUMBER` (the actual phone number in E.164 format). Both are needed; they serve different purposes.
- WhatsApp Cloud API **cannot post to groups.** Don't try to add a "send to group" button — only admin-paste works. (`whatsapp-web.js` could, but we walked away from that path on purpose.)
- Meta's `statuses` callbacks come AFTER the message API call. If a send "succeeds" in our logs (Meta accepted it) it might still fail delivery — check `BotEvent` rows with `action='wa_status'` and `payload.status='failed'` for the real verdict.
- `BotEvent.wa_message_id` is the idempotency key. Meta retries webhooks on non-2xx; our handler always returns 200 and uses `IntegrityError` from the unique constraint to detect duplicates and silently skip the second processing.
- Inbound message text from Meta arrives **as the user typed it** (including the mobile keyboard's auto-capitalisation — `NO` becomes `No`). `_extract_text` preserves case; comparison code lowercases at the point of use.

## Render Deploy Notes

- `master` is the deploy branch. Work happens on `stage`; PRs merge stage → master.
- Render auto-deploys on push to master. Build takes ~1-2 min.
- If a Cloud API change doesn't seem live after deploy, check Render → service → **Deploys** for the build status, and if needed, hit **Restart** to fork fresh gunicorn workers (which sometimes hold stale code on hot-deploys).
- Webhook URL in Meta dev console is hard-coded to `https://indcric.onrender.com/api/bot/whatsapp/`. Don't change it without also updating Meta.
