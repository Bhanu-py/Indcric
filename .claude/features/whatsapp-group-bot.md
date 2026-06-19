# WhatsApp Group-Resident Bot — Feature Spec

**Status:** Phase 0 spike **PASSED 2026-06-19** — SEND + READ both work end-to-end against a real group. Next: build Phase 1 (Django).

> **The fix that unblocked it (was blocked on an upstream bug):** published npm `whatsapp-web.js@1.34.7` cannot read events on live WhatsApp Web `2.3000.x` (no `message`/`message_reaction`/`vote_update`; `Client.inject` crashes). Per issue [#127084](https://github.com/pedroslopez/whatsapp-web.js/issues/127084): use **NO `webVersionCache`**, delete `node_modules`/`.wwebjs_auth`/`.wwebjs_cache`, then `npm install github:pedroslopez/whatsapp-web.js#main` (the unreleased patch; commit `2dc9466`, still self-reports 1.34.7). On a server use Puppeteer's bundled Chrome, not system Chromium. Reverses the earlier "walked away from whatsapp-web.js" decision in [whatsapp-bot.md](whatsapp-bot.md).
**Owner:** Bhanu
**Created:** 2026-06-18
**Decided by:** multi-agent design pass (library / hosting / integration / ban-risk / product) + adversarial critique.

> This bot is the **only** way to post into a WhatsApp *group* — the Meta Cloud API physically cannot. It complements (does not replace) the existing Cloud-API DM flow. Read [whatsapp-bot.md](whatsapp-bot.md) for the Cloud-API groundwork this reuses.

## Goal

Make the club's WhatsApp Community sub-group a two-way surface for IndCric:
- **Auto-post** session/RSVP/result/cost-split updates into the group.
- **Read** members' in-group `YES`/`NO` replies + commands back into Django.

Replaces the manual "admin copy-pastes a wa.me invite" flow. Django stays the source of truth; a small always-on Node bot (whatsapp-web.js + dedicated SIM) is the group-posting arm.

**Send-into-one-group + read-replies only.** No cold DMs, no contact scraping. ~3–5 posts per session lifecycle.

### Success criteria
- New poll → RSVP invite posts to the group within ~30s.
- Group `YES`/`NO` reply → `Vote` row, identical to the Cloud-API DM path.
- Bot's WhatsApp session survives VM reboot/redeploy with **zero re-scans**.
- A bot-number ban is a recoverable inconvenience (re-link spare SIM), never data loss — the group is owned by a human admin.

## Architecture

> **Correction vs the design draft:** IndCric's Django runs on an **always-on (paid) Render server** — it does NOT sleep. So the keepalive concerns in the draft are dropped, and Django *could* push to the bot. We still choose **Node-pulls-from-a-queue** — not for sleep reasons, but because the bot lives on a free VM behind NAT with no managed TLS, so making it publicly reachable for Django→Node push is the harder, more fragile half. The always-on bot pulling work from the always-on Django is the simplest reliable pattern.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  IndCric Django (always-on Render)  — SOURCE OF TRUTH             │
   │                                                                   │
   │  signals.py ── on_poll/on_session/on_match/on_donation           │
   │       │   safe_emit() ALSO enqueues ──►  OutboundMessage (queue)  │
   │       │                                   status: pending/claimed │
   │       │                                           /sent/failed    │
   │  apps/notifications/views_bot.py (NEW)                            │
   │   GET  /api/bot/outbound/        ◄── claim pending rows           │
   │   POST /api/bot/outbound/ack/    ◄── mark sent / failed           │
   │   POST /api/bot/inbound/         ◄── group replies / RSVPs        │
   │   POST /api/bot/heartbeat/       ◄── liveness ping (NEW)          │
   │     outbound/ack auth: ?token=$BOT_WEBHOOK_TOKEN                  │
   │     inbound auth:       ?token=$BOT_INBOUND_TOKEN (separate)      │
   │   BotEvent  (audit log, unique wa_message_id) — unchanged role    │
   └───────────────▲───────────────────────────────┬──────────────────┘
                   │ HTTPS poll ~25s                │ HTTPS POST
       (1) GET outbound  (2) POST ack               │ (3) POST inbound
                   │                                 │
   ┌───────────────┴───────────────────────────────┴──────────────────┐
   │  Node bot (whatsapp-web.js)  — ALWAYS ON, Oracle Cloud A1 VM.     │
   │  PM2-supervised. Holds the persistent WA Web session.            │
   │   poll loop ──► client.sendMessage(WA_GROUP_JID, body)           │
   │   on('message') ──► forward group YES/NO + commands to /inbound/ │
   │   RemoteAuth(store) ──► session in Mongo Atlas (survives reboot) │
   └───────────────────────────────┬───────────────────────────────────┘
                                    │ WhatsApp Web protocol (WebSocket)
                                    ▼
                  WhatsApp Community → one linked sub-group (…@g.us JID)
```

### Hosting: Oracle Cloud Always Free (A1 ARM)
- A1 ARM: 2 OCPU / 12 GB RAM / 200 GB persistent disk, always-on. Runs whatsapp-web.js's headless Chromium comfortably (install system `chromium`, set Puppeteer `executablePath`).
- **Cost honesty (per critique):** Oracle Always Free **requires a card** for identity verification; A1 ARM capacity is frequently "Out of host capacity" in popular regions (can block creation for days); Oracle may reclaim idle Always-Free compute. Treat "I can get an A1 box in my region" as a live risk, not a given. Fallback: Baileys on a 1 GB `e2-micro` (no Chromium).
- Django stays on Render, unchanged.

### Library: whatsapp-web.js (final pick)
- On a 12 GB box, the Chromium footprint — its only real downside — is a non-issue. Baileys' sole advantage (tiny RAM) doesn't matter here.
- Higher-level API (`client.sendMessage`, `GroupChat` helpers) and **built-in `RemoteAuth`** session persistence (Mongo/S3) — solves redeploy-survival with no custom auth-state code.
- Actively maintained (v1.34.7, Apr 2026), low open-issue backlog (~21 vs Baileys ~277), large tutorial ecosystem.
- **Communities caveat (both libs):** neither models WhatsApp *Communities* as first-class. Target **one linked sub-group by its `<number>@g.us` JID**, never "the community" as a unit.

## Two-Number Architecture (LOCKED 2026-06-18)

**Hard constraint discovered during Phase 0:** a Meta **Cloud-API** number **cannot be added to WhatsApp groups** ("this business can't be added to groups" — no setting fixes it). A phone number is on the Cloud API **XOR** the consumer/Business app, never both.

So IndCric uses **two separate numbers**:

| | Number A — "ICG" (existing) | Number B — group bot (new SIM) |
|---|---|---|
| Platform | Meta **Cloud API** | Regular **WhatsApp app** (consumer) |
| Can join groups? | ❌ No (barred by Meta) | ✅ Yes |
| Role | 1:1 DM features (`BALANCE`, leftover Cloud-API flow) | whatsapp-web.js group bot — posts + reads the group |
| Linked how | `WHATSAPP_PHONE_NUMBER_ID` / access token | QR scan via Linked Devices |
| **Must NOT** | be added to groups | **ever be registered on the Cloud API / Meta Business** |

Number B is a fresh dedicated SIM, set up on the **plain WhatsApp app** (not the API, not even strictly the Business app). If it ever gets registered on the Cloud API it hits the same group wall — keep it consumer-only.

## Session & Onboarding

### Dedicated-SIM QR-scan (one-time, human-driven)
1. Register **Number B** (the new dedicated SIM) on the **plain WhatsApp app** — **never on the Meta Cloud API / Business Platform** (that's what poisons a number for groups). Set a real name + photo; **warm it up as a normal phone for 1–2 weeks** (some human chats) before any bot activity — biggest behavioural ban-risk reducer.
2. A **human admin** owns the Community + target sub-group, then adds the bot's number as an ordinary member. Admin keeps ownership so the group survives a bot ban.
3. Start the Node bot on the A1 VM interactively; it emits `'qr'` → render with `qrcode-terminal`.
4. On the dedicated phone: WhatsApp → **Linked Devices → Link a Device → scan**. `'authenticated'` → `'ready'` fire.
5. Capture the group JID once: on `'ready'`, `client.getChats()`, filter `chat.id.server === 'g.us'`, log `chat.id._serialized`, store as `WA_GROUP_JID`. (Prefer `getChats()`+filter over `getChatById`, which can return a `PrivateChat`.)

### Session persistence — `RemoteAuth` + Mongo Atlas M0
```js
new Client({
  authStrategy: new RemoteAuth({
    clientId: 'indcric-bot',
    store,                        // wwebjs-mongo MongoStore
    backupSyncIntervalMs: 300000  // 5-min backup
  }),
  puppeteer: { headless: true, executablePath: process.env.CHROMIUM_PATH }
});
```
- Mongo Atlas M0 is free + no card. **Caveat:** M0 auto-pauses after ~60 days of *zero* activity — our 5-min backups keep it warm, so fine.
- `'remote_session_saved'` fires ~1 min after `'ready'`; log it to confirm persistence before relying on it.

### Reconnect / supervision
- Run under **PM2** (`pm2 start bot.js --name indcric-bot`, `pm2 save`, `pm2 startup`).
- **Distinguish two failure classes (per critique — this matters):**
  - **Process crash / transient disconnect** → `client.destroy()` then `client.initialize()`; `takeoverOnConflict:true`, `restartOnAuthFail:true`; ~9s graceful shutdown so Chrome flushes IndexedDB.
  - **`'disconnected'` with reason `LOGOUT` / `'auth_failure'`** → WhatsApp invalidated the session. PM2 **cannot** self-heal this. Do NOT loop-restart. Flip a Django-visible `bot_logged_out` flag, alert the admin, and require a human QR re-scan with the physical SIM phone.
- The linked device dies if the **physical SIM phone is offline >14 days** — keep it charged + online.

## What the Bot Posts

Ranked by value, anti-fatigue first. ~3–5 group posts per session lifecycle. Each enqueued with a `dedup_key` so re-saves post at most once.

**1. Poll open — RSVP call (HIGH, interactive).** `on_poll(created)` (merge with `on_session(created)` — suppress the latter). Back-filled past session → nothing. `dedup_key=poll_opened:{poll.id}`.
```
🏏 *{session.name}* — who's in?
📅 {date:%a %d %b} · {time:%H:%M}
📍 {session.location}{cost_line}

Reply *YES* or *NO* right here 👇
Details: {session_url}
```
> ⚠️ **Do NOT reuse `build_group_invite_text`** — it emits wa.me *deep-link* text ("RSVP by tapping below"), which contradicts "reply here" and defeats the two-way premise. Add a **new composer `build_group_rsvp_text(poll, site_url)`** with the template above. Test asserts the body contains "Reply" and not "tapping below".

**2. Attendance confirmed — cost split (HIGH, read-only).** `on_session` False→True `attendance_confirmed` with `cost_per_person` set. Free sessions → nothing. `dedup_key=session_confirmed:{session.id}`.
```
💰 *{session.name}* is settled — €{cost_per_person:.2f} per player.
📅 played {date:%a %d %b}

Check your share + pay: DM me *BALANCE*, or open {session_url}
```

**3. Match result (HIGH, read-only).** `on_match`: completed + winner/tie. `dedup_key=match_result:{match.id}`.
```
🏆 *{winner.name}* won {match.name}!
{scoreline}
📋 Scorecard: {match_url}
```

**4. Donation (MEDIUM, GATED).** `on_donation(created)`, only **≥€20 OR crossing a 25/50/75/100% milestone**. Bank micro-donations stay in-app. Respects anonymity. `dedup_key=donation:{donation.id}`.
```
❤️ *{display_name}* donated €{amount:.2f}{campaign_suffix} — thank you! 🙏
{progress_line}
Chip in: {support_url}
```

**5. Teams announced (MEDIUM, read-only).** From `save_teams_view` (add enqueue — no signal there today). Both teams populated. `dedup_key=teams:{session.id}`. **Length-guard** the player lists (WhatsApp ~4096-char cap).
```
📋 Teams for *{session.name}* ({date:%a %d %b})
🔵 {teamA.name} (c: {teamA.captain})
{teamA_players}
🔴 {teamB.name} (c: {teamB.captain})
{teamB_players}
See you on the pitch! {session_url}
```

**6. Pre-session reminder (MEDIUM, interactive).** Scheduled job (reuse the existing `run_reminders` cron). **One reminder per session, only if non-voters remain.** Drop the old 24h/morning/2h cadence (that was the fatigue source).
```
⏰ *{session.name}* is tomorrow ({time:%H:%M}, {location}).
Still need: {nonvoter_count} replies. Reply *YES*/*NO* if you haven't 👇
```

**IN-APP ONLY (never group-posted):** individual votes (`on_vote`) and individual payments (`on_payment`) — one-per-person would flood the group. Group sees aggregates on demand via `WHO`/`STATUS`.

## What the Bot Reads

Node `on('message')` (filtered to `WA_GROUP_JID`) → `POST /api/bot/inbound/`. Django reuses the existing parse/dispatch pipeline.

- **RSVP parse:** reuse `RSVP_PATTERN` (`^\s*(yes|no|y|n|✅|❌|1|2)\s*(?:[#\s]*(\d+))?\s*$`, IGNORECASE). session_id → that poll; else latest open poll. `Vote.objects.update_or_create`.
- **Phone→User:** Node strips group author `<number>@c.us` to E.164 with leading `+`; Django's `_normalize_inbound_phone` re-adds defensively. `User.objects.filter(phone=phone)`.
- **Commands:** `YES/NO[ <id>]`, `BALANCE/BAL/WALLET`, `STATUS/POLL/WHO/COUNT`, `HELP/?` (reuse existing dispatcher).
- **Idempotency:** Node sends a stable `wa_message_id` (`msg.id._serialized`); `BotEvent` unique constraint swallows duplicate deliveries.

> ⚠️ **Group replies must route to the group, never a DM (per critique — this is bigger than one call site).** The existing handlers call `send_text_message(phone, …)` (a Cloud-API DM) in **8+ branches** (`not_recognised`, `no_active_poll`, balance/status/help/unknown, …). If only `_handle_rsvp` is rerouted, a group member typing `HELP` or RSVPing from an unregistered number triggers a Cloud-API DM to a closed 24h window — silent failure or a paid utility message.
> **Fix:** thread a `reply_sink` through `dispatch_inbound`. For `chat=='community'`, **every** handler reply enqueues an `OutboundMessage` to `WA_GROUP_JID` — none call `send_text_message`. Test: a group-origin `HELP` and a group-origin RSVP from an unknown phone both produce an `OutboundMessage` and **zero** Cloud-API calls.

## New Django Pieces

All under the existing `/api/bot/` prefix, `csrf_exempt`, JSON. Put in a new `apps/notifications/views_bot.py`. Factor the token check from `run_reminders_view` into `_check_bot_token(request, token_setting)`.

### New model — `OutboundMessage` (queue) in `apps/notifications/models.py`
```python
class OutboundMessage(models.Model):
    PENDING, CLAIMED, SENT, FAILED = 'pending', 'claimed', 'sent', 'failed'
    STATUS_CHOICES = [(PENDING,'Pending'),(CLAIMED,'Claimed'),(SENT,'Sent'),(FAILED,'Failed')]
    body          = models.TextField()
    target        = models.CharField(max_length=120, default='community')  # group JID/alias
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    dedup_key     = models.CharField(max_length=80, blank=True, default='')
    claimed_at    = models.DateTimeField(null=True, blank=True)
    sent_at       = models.DateTimeField(null=True, blank=True)
    wa_message_id = models.CharField(max_length=100, blank=True, default='')
    error         = models.CharField(max_length=255, blank=True, default='')
    attempts      = models.PositiveSmallIntegerField(default=0)
    created_at    = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
        constraints = [models.UniqueConstraint(
            fields=['dedup_key'], condition=~models.Q(dedup_key=''),
            name='uniq_outbound_dedup')]
```
Register in admin with `list_filter = ('status','target')`. `BotEvent` stays the audit log (no status/claim fields — can't be the queue).

### Endpoints (`apps/notifications/urls.py`)
```python
path('api/bot/outbound/',     views_bot.outbound_drain,  name='bot_outbound'),
path('api/bot/outbound/ack/', views_bot.outbound_ack,    name='bot_outbound_ack'),
path('api/bot/inbound/',      views_bot.inbound_message, name='bot_inbound'),
path('api/bot/heartbeat/',    views_bot.heartbeat,       name='bot_heartbeat'),
```
1. **`GET /api/bot/outbound/`** — in `transaction.atomic()`: `select_for_update(skip_locked=True).filter(status='pending')`, set **`status='claimed'`, `claimed_at=now`**, return `[{id,body,target}]`. (Claiming as a distinct status, not just stamping `claimed_at`, is what prevents duplicate re-sends — see below.)
2. **`POST /api/bot/outbound/ack/`** — `{id,status:'sent',wa_message_id}` → `sent`, write outbound `BotEvent`; `{id,status:'failed',error}` → `failed`, `attempts+=1`.
3. **`POST /api/bot/inbound/`** — `{from,wa_message_id,text,chat,author_name}` → `dispatch_inbound(...)` with `reply_sink` routing group replies to the queue.
4. **`POST /api/bot/heartbeat/`** — Node pings each poll; stores `last_seen`. Backs the dead-man's-switch alerting (below).

### `_process_message` refactor (per critique — half-day, not a rename)
Current `_process_message(msg, value)` reads a Meta-webhook-shaped dict. Extract a shared `dispatch_inbound(wa_message_id, phone, text, chat, reply_sink)` callable from both the Meta webhook and `/api/bot/inbound/`. **Write a characterization test for the existing Meta path first** so the refactor is provably behaviour-preserving; build a synthetic `raw` payload for the group path so `BotEvent.payload` stays consistent.

### Stuck-claim reclaim (per critique — prevents duplicate posts)
If the bot crashes after claiming but before acking (likely on a Chromium OOM mid-send), the row is stuck `claimed`. `outbound_drain` also re-claims rows where `status='claimed' AND claimed_at < now - 90s`. Node additionally refuses to re-send a row whose `wa_message_id` it already recorded locally.

### Env vars
**Django (Render):** reuse `BOT_WEBHOOK_TOKEN` (outbound/ack); **add `BOT_INBOUND_TOKEN`** (separate, higher-trust — the inbound endpoint *writes Vote rows*, so don't gate it with the read-only token). `SITE_URL` already present.

**Node (Oracle VM `.env`):**
| Var | Purpose |
|---|---|
| `INDCRIC_BASE_URL` | `https://indcric.onrender.com` |
| `BOT_WEBHOOK_TOKEN` | outbound/ack/heartbeat |
| `BOT_INBOUND_TOKEN` | inbound |
| `WA_GROUP_JID` | target sub-group `…@g.us` |
| `POLL_INTERVAL_MS` | `25000` |
| `CHROMIUM_PATH` | system Chromium on the A1 box |
| `MONGODB_URI` | RemoteAuth store |
| `RA_CLIENT_ID` | `indcric-bot` |

## Operational Safety (the part that actually keeps it alive)

The single biggest risk is **the bot dies and nobody notices for days** — PM2 restarts a *process* but can't fix a logged-out session, an OOM-looping Chromium, or a banned number. While down: outbound rows pile up `pending`; **inbound RSVPs are lost permanently** (WhatsApp doesn't replay missed linked-device messages).

**Mandatory before relying on it:**
- **Dead-man's-switch:** Node hits `/api/bot/heartbeat/` each poll. A separate external cron (cron-job.org) checks `last_seen` and pending-count, alerts the admin (email/Telegram) when `last_seen > ~3 poll intervals` OR a row is `pending > 5 min`.
- **Surface session state:** push `'remote_session_saved'` and `'disconnected'`(LOGOUT) to Django so a logged-out bot is *visible*, not just a healthy-looking PID.
- Because Django is always-on, the in-app feed + Cloud-API DM path keep working even when the group bot is dead — graceful degradation, not total outage.

## Ban-Risk Mitigation

Risk for *this* use case (one private group, ~30–50 known members, ~20–50 msgs/week, no cold outbound) is **LOW-to-MEDIUM** — the two heaviest triggers (cold outbound, low reply-ratio) are absent.

**DO:** dedicated SIM you own; warm up 1–2 weeks as a real phone; ramp bot activity over ~7 days; keep all activity in the ONE consenting group; randomized Gaussian-jitter delays + typing simulation; vary wording; human admin owns the group; spare SIM + re-link runbook ready.

**DON'T:** cold-DM anyone; bulk-blast identical messages; auto-add members / scrape contacts; install random "anti-ban" npm packages (the `lotusbail` package was caught exfiltrating sessions, Apr 2026); store anything critical only in the bot account; resume full activity right after a temp ban lifts.

> ⚠️ **Datacenter-IP contradiction (per critique):** Oracle A1 is a datacenter IP, which violates the "don't run on datacenter IPs" guideline and raises the fingerprint. Either **accept this in writing** (low real risk at our volume) or route the bot's WA traffic through a **residential proxy / the admin's home connection** (changes the hosting calculus). Decide explicitly.

## Cost Reality (blunt)

Recurring **cash** cost is plausibly €0, but not trap-free:
- **Oracle A1:** card required for identity; A1 capacity often unavailable in-region; idle-reclaim risk. Biggest asterisk.
- **Mongo Atlas M0:** free, no card; auto-pauses after ~60 days *zero* activity (our backups prevent this).
- **Dedicated SIM:** needs to stay active — many prepaid SIMs deactivate without periodic top-up, which would silently kill the bot.
- **Hidden cost = admin time:** a ban = 1–2 week feature outage + re-warm a new SIM. whatsapp-web.js also breaks for a day or two after some WhatsApp protocol updates, independent of bans.

## Phased Build Plan

### Phase 0 — Local spike — ✅ PASSED 2026-06-19
Throwaway Node script + `LocalAuth`, QR-scan dedicated SIM against a **private test group**. Log every `chat.id._serialized`; confirm `sendMessage` posts and `on('message')` fires for replies. **Exit:** send + read works end-to-end on a laptop.

**Result (after the git-main fix above):** Two-number setup confirmed — Number B (`+32465110367`) linked via QR against the "App development" test group; `getChats()` listed groups; bot posted both the text RSVP prompt and a native Poll (**SEND ✅**). With multiple real members testing (**READ ✅**):
- **Typed `YES`/`NO`** (`message`) — rock solid, fired every time; bot reacted ✅/❌ correctly; `!ping`→`pong` worked.
- **Native WhatsApp Poll** (`vote_update`) — works reliably; both voters logged with correct number + selection. The most fragile event is solid on `main`.
- **Reactions** (`message_reaction`) — fire, but with **two gotchas Phase 1 MUST handle:** (1) **skin-tone modifiers break equality** — a member's `👍🏾` failed the bare `=== '👍'` check and a valid YES was dropped; normalize emoji to base codepoint before matching. (2) **the bot sees its OWN reactions echoed** (`message_reaction` author == bot number); ignore events whose author is the bot's own number.

**Recommended input mechanism (Phase 1):** native Poll as primary (lowest friction, free tally, `vote_update` proven) + typed `YES`/`NO` always supported as the robust fallback; reactions secondary (only if emoji-normalized + self-filtered). **Exit met.**

### Phase 1 — Receive (group → Django) — 🟢 DJANGO SIDE BUILT 2026-06-19
Django: `OutboundMessage` model + migration; `_check_bot_token` helper; **`clean_phone` normalization** (handover #4 — ship before group rollout); characterization test for the Meta path; refactor `_process_message` → `dispatch_inbound` with `reply_sink`; `POST /api/bot/inbound/`; split `BOT_INBOUND_TOKEN`. Node: filter to `WA_GROUP_JID`, strip author to E.164, POST inbound. **Exit:** a group `YES`/`NO` records a `Vote` and a confirmation posts **in the group**; group `HELP` from an unknown number makes zero Cloud-API calls.

**Built (Django, on `stage`, uncommitted):**
- `OutboundMessage` queue model (`apps/notifications/models.py`) + migration `0005_outboundmessage.py`; admin with `list_filter=('status','target')`.
- `dispatch_inbound(wa_message_id, phone, text, chat, reply, raw)` extracted in `views.py`; every handler (`_handle_rsvp/balance/status/score/history/help/unknown`) now takes an optional `reply` sink (defaults to the Cloud-API DM, so the Meta path + existing tests are unchanged). `_process_message` is now a thin Meta→dispatch adapter.
- `_check_bot_token(request, token_setting)` helper (factored from `run_reminders_view`, fails closed); `BOT_INBOUND_TOKEN` added to settings (separate from `BOT_WEBHOOK_TOKEN`).
- `POST /api/bot/inbound/` in new `apps/notifications/views_bot.py`: auth via `BOT_INBOUND_TOKEN`; accepts `kind` = `text|reaction|poll_vote`; **emoji-normalizes** (strips skin-tone modifiers + U+FE0F so `👍🏾`==`👍` — Phase 0 bug) and maps 👍/✅→yes, 👎/❌→no; **ignores the bot's own number** (self-reaction echo); RSVP → records `Vote` + returns a `{type:'react',emoji}` action (no per-vote text); commands → enqueue `OutboundMessage` to the group; idempotent via `BotEvent.wa_message_id`.
- `clean_phone`: `_normalize_phone` (accounts/forms) now strips internal spaces/dashes/parens → canonical `+<digits>`.
- Tests: Meta-path characterization + 7 group-inbound tests (vote record, skin-tone reaction, poll vote, unknown-HELP→queue+zero Cloud calls, self-ignore, idempotency, auth).

**NOT yet built:** the Node side (poll `WA_GROUP_JID`, strip author→E.164, POST `/api/bot/inbound/`, perform the returned `react` action) — that's wired in Phase 2 alongside the outbound drain. **RSVP confirmation is emoji-react (returned as an action); command replies queue as text** — matches the locked decision.

### Phase 2 — Post (Django → group)
Django: `outbound_drain` (with claimed-status + reclaim window) + `outbound_ack`; new `build_group_rsvp_text` composer; enqueue from `on_poll`/`on_session`(confirmed)/`on_match`/gated `on_donation`/`save_teams_view`; admin `list_filter`. Node: poll loop → send → ack, Gaussian jitter; local re-send guard. **Exit:** creating a poll auto-posts the invite within ~30s; dedupe prevents reposts; crash-after-claim doesn't double-post.

### Phase 3 — Production hardening
Provision Oracle A1; install Chromium; PM2 + `startup`/`save`. Switch to `RemoteAuth` + Mongo Atlas; confirm `'remote_session_saved'`; reboot VM → verify **no re-scan**. LOGOUT-vs-crash split handling + admin re-scan runbook. Dead-man's-switch heartbeat + external alerting. Failed-`OutboundMessage` sweep (`attempts<3`). Scheduled single reminder (reuse `run_reminders` cron). 7-day warmup. **Exit:** survives redeploy + VM reboot with zero manual re-scan; failures alert + retry.

## Decisions

**Locked (2026-06-18):**
- ✅ **Bot IP:** accept Oracle A1's datacenter IP — low real risk at our volume. No residential proxy.
- ✅ **Group-reply style:** **emoji-react only** (bot reacts ✅/❌ to the member's RSVP message). Quietest; no per-RSVP message clutter. This means the `reply_sink` for group RSVPs is a *reaction*, not a queued text post — text posts are reserved for command replies (HELP/STATUS/etc.) and the auto-posts.
- ✅ **Kickoff:** Phase 0 spike first (see [bot/](../../bot/)).

**Locked (2026-06-19):**
- ✅ **Group vote inputs = native poll + 👍/👎 reactions on the bot's own message ONLY.** Typed `yes`/`no` in the group is **NOT** counted as a vote — members say yes/no in normal conversation, which produced false RSVPs. Implemented via `dispatch_inbound(allow_text_rsvp=False)` for group text; the group also never gets an "I didn't understand" reply (`reply_unknown=False`). Group text is only ever a *command* (HELP/STATUS/…). DMs to the bot still accept typed `YES <session_id>` (the deep-link path is unambiguous). The Node client must therefore only forward `kind='reaction'` for reactions on the bot's RSVP message and `kind='poll_vote'` for its poll — not arbitrary group text as votes.

**Still open (revisit before the phase they gate):**
- **Session store** (Phase 3): Mongo Atlas M0 (recommended) vs S3 vs Neon Postgres custom store.
- **Donation gate** (Phase 2): keep €20 / 25-50-75-100% milestones?
- **Reminder timing** (Phase 3): single reminder at T-24h vs T-12h; quiet hours?
- **Hosting confirmation** (Phase 3): provision Oracle A1, or fall back to Baileys-on-`e2-micro`?
- **Multi-group future:** ever more than one target group? (`OutboundMessage.target` already carries a JID per row, so extensible.)
- **Alerting channel** (Phase 3): dead-man's-switch alert via email, Telegram, or WhatsApp to the admin?

### Emoji-react implications (from the locked reply-style decision)
- Group **command** (`HELP`, `STATUS`, `BALANCE`, unknown text) → needs a text answer; that enqueues an `OutboundMessage` to the group (infrequent, so noise is acceptable).
- Unknown-number RSVP → react with a neutral ❓ and stay silent, OR a one-time terse "not registered" reply rate-limited per number. Decide during Phase 1.

## How members VOTE (input mechanism) — open, decided by the Phase 0 spike

The user's preferred model: **bot posts the session once; members REACT (👍 yes / 👎 no); the bot reads the reactions and records `Vote` rows; Django updates.** Technically feasible — whatsapp-web.js fires `message_reaction` with `senderId` (→ `User.phone`), `reaction` (emoji; `''` on removal), and `msgId` (→ which poll). One reaction per person per message maps cleanly to one vote; reaction-change → vote-change; reaction-removed → withdraw.

Three candidate input mechanisms, being tested head-to-head in the Phase 0 spike ([bot/spike.js](../../bot/spike.js)) because event reliability on an unofficial client can only be confirmed empirically:

| Mechanism | Event | Friction | Native tally | Reliability risk |
|---|---|---|---|---|
| Typed `YES`/`NO` | `message` | High (type+send) | No | Lowest — robust |
| **Reactions 👍/👎** | `message_reaction` | Low for 👍, **high for 👎** | No | Medium |
| **Native Yes/No Poll** | `vote_update` | Lowest (equal taps) | **Yes** | **Highest — must verify** |

**Key finding:** WhatsApp's quick-react bar is fixed (👍 ❤️ 😂 😮 😢 🙏) — **👎 is NOT one-tap** (requires "+" → search). So "👍 yes / 👎 no" is lopsided; expect lots of 👍 and few explicit 👎. The **native Poll** avoids this (both options equal one-tap) and gives a free live tally — *if* `vote_update` fires reliably in the group, which is the open question.

**Decision rule:** after the spike, pick the mechanism that logged **every** vote/change reliably. Likely outcome — native Poll if `vote_update` is solid; else reactions (accepting 👎 friction) with typed YES/NO always supported as the robust fallback. If reactions win, only 👍 reliably means "yes"; treat absence/👎 carefully rather than assuming silence = no.

Whichever wins, the Django mapping is identical: voter phone → `User` → `Vote.update_or_create`; removal/deselect → withdraw. The `/api/bot/inbound/` payload gains a `kind` field (`text` | `reaction` | `poll_vote`) so `dispatch_inbound` knows how to interpret it.
