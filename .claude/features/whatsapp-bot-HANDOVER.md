# WhatsApp Bot — Handover (Cross-Machine)

**Last updated:** 2026-05-22
**Status:** Planning complete, no code written yet.
**Resume on:** New computer, fresh clone.

> Read [whatsapp-bot.md](whatsapp-bot.md) first — it has the full feature spec, tier plan, and architectural decisions. This file is just the cross-machine pickup checklist.

## Where We Left Off

- ✅ Feature spec written ([whatsapp-bot.md](whatsapp-bot.md))
- ✅ Tier 1/2/3 scope agreed — start with Tier 1 (RSVP + payment nudges + balance lookup)
- ✅ Stack decided: Node.js + `whatsapp-web.js`, Django webhook glue, bot lives in club's **WhatsApp Community** sub-groups
- ✅ Community model accounted for: announcements group is admin-write-only, sub-groups are normal; `WhatsAppGroup` table will map `wa_group_id` → audience
- ❌ No code changes yet — `User.phone`, `WhatsAppGroup`, `BotEvent` models all still TODO
- ❌ No Node bot project initialised
- ❌ Open questions in spec still unanswered (pilot sub-group, bot admin status, number choice, opt-in, UPI strategy)

## New-Machine Setup Checklist

### 1. Django app (already exists in this repo)

```powershell
# Clone
git clone <your-remote> c:\GCC\Indcric
cd c:\GCC\Indcric

# Python venv
python -m venv .venv
.venv\Scripts\activate

# Deps
pip install -r requirements.txt

# Local Postgres
docker-compose up -d

# .env — recreate from this template (not committed):
#   DEBUG=True
#   db_hostname=localhost
#   db_databasename=indcric_db
#   db_username=indcric_user
#   db_password=indcric_password
#   BOT_WEBHOOK_TOKEN=<generate a long random string — share between Django and the Node bot>

# Migrate + run
python manage.py migrate
python manage.py runserver
```

### 2. Node bot project (does NOT exist yet — create it)

Decide on location: either a **sibling repo** (`Indcric-bot/`) or a **subdirectory** (`Indcric/bot/`). Sibling repo is cleaner — different language, different deploy lifecycle.

```powershell
# When you're ready to start step 4 of Next Steps in the spec:
mkdir c:\GCC\Indcric-bot
cd c:\GCC\Indcric-bot
npm init -y
npm install whatsapp-web.js qrcode-terminal axios dotenv

# .env for the bot:
#   DJANGO_WEBHOOK_BASE=http://localhost:8000/api/bot
#   BOT_WEBHOOK_TOKEN=<same value as Django>
#   ALLOWED_COMMUNITY_ID=<filled in after first QR scan>
```

First run will print a QR code in the terminal — scan it from the bot's WhatsApp account on phone. The session file (`.wwebjs_auth/`) will be created locally and lets the bot resume without re-scanning. **This session file is per-machine** — you'll need to re-scan on each new computer.

## Files to Read First (in order)

1. [.claude/features/whatsapp-bot.md](whatsapp-bot.md) — full spec
2. [cric/models.py](../../cric/models.py) — current `User`, `Session`, `Poll`, `Vote`, `Wallet`, `Payment` models
3. [cric/views_polls.py](../../cric/views_polls.py) — how votes are currently written (so the webhook mirrors the same flow)
4. [cric/urls.py](../../cric/urls.py) — where to register `/api/bot/...` routes
5. [.claude/skills/session-workflow/SKILL.md](../skills/session-workflow/SKILL.md) — session state machine the bot will hook into

## Decisions Still Pending (Resolve Before Tier 1.2)

Pulled from the spec's Open Questions — answer these before building payment DMs:

1. **Pilot sub-group:** Which single sub-group does the bot join first?
2. **Bot admin status:** Will the bot account be made Community admin (so it can post Announcements)? If no → all posts go to the pilot sub-group.
3. **Bot phone number:** Dedicated SIM or virtual? Have a backup number ready in case of ban.
4. **Opt-in flow:** Is being in the group sufficient consent, or do we require `/optin` before DMs?
5. **UPI:** Static per-user UPI ID on the profile, or generated per-payment with amount pre-filled?

For Tier 1.1 (RSVP only) you can defer 3–5 and just pick the pilot sub-group.

## Resume Here

When you sit down on the new machine, **the first concrete task** is Step 1 of the spec's Next Steps:

> Add `phone` field to `User` — migration + admin field. Unique, indexed, nullable for existing users.

Concretely:

- Edit [cric/models.py](../../cric/models.py) — add `phone = models.CharField(max_length=20, unique=True, null=True, blank=True, db_index=True)` to the `User` model.
- `python manage.py makemigrations cric && python manage.py migrate`
- Register the field in [cric/admin.py](../../cric/admin.py) under the User admin's `fieldsets`.
- Add it to [cric/forms.py](../../cric/forms.py) `ProfileForm` so users can self-edit (mobile keyboard `type="tel"`).
- Update the profile page template under [cric/templates/cric/pages/](../../cric/templates/cric/pages/) to show + edit the phone field.

After that, move to Step 2 (WhatsAppGroup model) — then Step 3 (BotEvent) — then start the Node bot.

## Things to NOT Forget

- `BOT_WEBHOOK_TOKEN` must be identical in Django `.env` and bot `.env`. Generate it once, store both.
- Phone numbers must be normalised before lookup — strip spaces, add country code if missing. Pick a format (E.164: `+919876543210`) and enforce it at the model layer or in a clean method.
- The bot session file (`.wwebjs_auth/`) is **not** portable across machines reliably — plan to re-scan QR on each new dev machine. Production hosting needs a persistent volume for this directory.
- WhatsApp Community parent-group ID is exposed via `chat.groupMetadata.parentGroup` in `whatsapp-web.js` — use this for "is this our club?" checks, not individual group IDs.
