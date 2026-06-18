# WhatsApp Bot — Club Community POC

**Status:** Live on Meta Cloud API. Pivoted from broadcast-DM to free group-share flow on 2026-05-28 to avoid utility-conversation charges.
**Owner:** Bhanu
**Created:** 2026-05-13
**Last pivot:** 2026-05-28 — see "Cost Pivot" section below

## Goal

Run a bot inside the IndCric club's WhatsApp community/groups that talks to the existing Django app — so the group itself becomes a UI layer for RSVPs, payments, balances, and expense tracking. Cut down the manual "who's coming / who paid" chase that currently happens in chat.

## Cost Pivot (2026-05-28)

We initially built broadcast template DMs (`notify_poll_created`) using Meta Cloud API. Meta classifies these as **utility conversations**, which are paid (~€0.038–€0.085 each in Belgium) — not part of the 1000/month free service-conversation allowance. Meta blocked our first sends with error 131042 ("Business eligibility payment issue") because no payment threshold was set; they asked for ~$20 upfront.

**Resolution:** stopped automatic broadcasts and routed RSVPs through the free 24-hour service window instead.

- An admin pastes a formatted session message into the **WhatsApp Community group** (free — group messages aren't billed at all on the Cloud API; this works because the admin sends it from their own WhatsApp, not from the bot).
- The message contains `wa.me/<bot-number>?text=YES%20<session_id>` deep links. Tapping one opens the bot DM with the choice pre-filled; the user sends.
- That inbound message opens a **free 24h service window**, during which the bot can reply, log the vote, send confirmations, answer balance queries, etc., all without charges.

Result: zero outbound utility charges at default volume. Paid broadcast functions (`notify_poll_created`, `resend_poll_invite`, `send_session_reminders`) still exist in `services.py` as escape hatches for emergencies but are no longer surfaced in the UI or called from the create-session/create-poll flows.

## Constraints & Assumptions (current, post-pivot)

- **Meta Cloud API only.** Cloud API cannot post messages to groups directly — only DMs. We work around this by having an admin paste the formatted invite message into the group manually; the message contains tap-to-RSVP `wa.me/` deep links so members can reply to the bot in DM with one tap.
- **Costs are real.** Service conversations (user-initiated, 24h window) are free up to 1000/month. Utility conversations (bot-initiated templates) are paid. The current architecture avoids utility conversations entirely.
- Django stays the **source of truth.** The bot is a thin I/O layer that webhooks back into the same Django models the web UI uses.
- WhatsApp users map to `User` rows via phone number (`User.phone`, indexed, E.164 with `+` prefix).
- `whatsapp-web.js` group-bot approach is **archived, not deleted** — see "Open Questions / Future" below. If we ever need true bot-posts-in-group behaviour without admin manual share, that's the path back.

## Capability Map (current Cloud-API architecture)

| Channel | Cost | Use |
|---|---|---|
| Admin pastes message into group (manual, from admin's WhatsApp) | Free | Session invite with tap-to-RSVP `wa.me` deep links |
| DM in (user → bot) | Free (opens 24h service window) | RSVP via deep link, balance lookup, help |
| DM out (bot → user, inside 24h service window) | Free (counts as service conversation) | Vote confirmation, balance reply, error/help messages |
| DM out (bot → user, **template / outside service window**) | Paid (~€0.038–€0.085 each) | Currently disabled — `resend_poll_invite` and `send_session_reminders` are the escape hatches |

## WhatsApp Community Model

The club uses a **WhatsApp Community** — a parent container with one **Announcements** group + multiple linked **sub-groups** (e.g. "Saturday Players", "Sunday Players", "Tournament Squad"). The bot will be added to the Community, which means it joins the Announcements group and any sub-groups it's invited to.

Key behavioural differences vs a plain group:

- **Announcements group is admin-write-only.** For the bot to post session announcements there, the bot's WhatsApp account must be a Community admin. Otherwise, post to a sub-group instead.
- **Sub-groups are normal groups.** RSVP replies, expense chat, score updates all happen in sub-groups.
- **Each sub-group has its own group ID.** Bot must handle being in N sub-groups simultaneously — store a `Group` table mapping `wa_group_id` → which `Session` audience this group represents.
- **Community ID is the umbrella.** `whatsapp-web.js` exposes `chat.groupMetadata.parentGroup` — use this to scope "is this message from our club's community?" rather than whitelisting individual group IDs.
- **Cross-posting risk:** If a player belongs to multiple sub-groups, naive broadcasts can hit them twice. Dedupe by `User.phone`, not by group.

Add a small `WhatsAppGroup` model so admins can map each sub-group to a default session-audience (or leave it general). Fields: `wa_group_id` (unique), `name`, `is_announcements` (bool), `default_audience` (FK or tag), `active` (bool).

## POC Scope — Tiered

### Tier 1 — Build first (highest leverage, smallest surface)

| Feature | IndCric model touched | Flow |
|---|---|---|
| **Group RSVP** | `Poll`, `Vote` | Bot posts session in group → members reply ✅/❌ or `/rsvp yes` → webhook writes `Vote` |
| **Payment DM nudges** | `Payment`, `Session.cost_per_person` | When session is `CONFIRMED`, bot DMs each unpaid player their share + UPI link |
| **Wallet balance lookup** | `Wallet` | User DMs `balance` → bot replies with `Wallet.amount` + last 3 transactions |

### Tier 2 — Build after Tier 1 is stable

| Feature | IndCric model touched | Flow |
|---|---|---|
| **Team announcement card** | `Team`, `SessionPlayer` | After `save_teams_view` runs, bot posts rendered team sheet to group |
| **Expense splitting via chat** | `Expense`, `ExpenseSplit` (planned) | `@bot split 1200 pizza` → creates `Expense` with equal splits, replies with each share |
| **Live score updates** | `Team.runs`, `Team.wickets` (planned) | Captain DMs `score TeamA 142/6` → bot updates DB + posts to group |

### Tier 3 — Nice-to-have

| Feature | IndCric model touched | Flow |
|---|---|---|
| Post-session attendance | `Attendance.attended` | Day after, bot DMs each RSVP'd player "Did you play?" |
| Stats query | `PlayerProfile` | `stats @bhanu` → matches/runs/wickets/catches |
| Admin session creation | `Session` | Admin DMs `new session Sat 7am ₹200 Indus Park` → creates row |

## Recommended Stack

- **Bot runtime:** Node.js + [`whatsapp-web.js`](https://wwebjs.dev/). Better docs and community than Baileys for a POC.
- **Hosting:** Azure container or B1s VM — needs a persistent session file across restarts. Free tier won't work (no persistent disk).
- **Glue:** Django webhook endpoints under `/api/bot/`. Token-auth via a shared secret in `.env` (`BOT_WEBHOOK_TOKEN`). All endpoints staff-scoped writes.
- **User mapping:** New `User.phone` field, indexed, unique. Bot looks up sender by phone; unknown numbers get a "register first" reply.

## Architectural Notes

- **Webhook endpoints, not REST API:** Keep the no-REST convention. Endpoints return small JSON (`{ok: true}`) just because the bot is the consumer, not the browser. They are not part of the user-facing app.
- **Atomic writes:** Any bot action that writes Payment + Wallet (e.g. mark-paid-from-wallet) wraps in `transaction.atomic()`.
- **Idempotency:** Bot may retry; webhooks use `get_or_create` keyed on `(user, session)` for votes/payments so duplicates are safe.
- **Rate limiting:** Bot must throttle outbound (e.g. DM nudges) — batch with delays of 3–5s to avoid ban.
- **Audit trail:** Every bot-driven mutation records `created_by=<bot system user>` or a dedicated `BotEvent` row, so we can trace anything back to a WhatsApp message ID.

## Open Questions

- **Community scope:** Pilot in one sub-group first, or join the full Community on day one? Recommended: one sub-group for Tier 1, expand after.
- **Bot admin status:** Will the bot's WhatsApp account be made a Community admin (so it can post to Announcements)? If not, all bot posts go to sub-groups.
- **Number choice:** Dedicated SIM/eSIM for the bot, or a virtual number? Affects ban-risk recovery — if the number is banned, we need a backup path.
- **Opt-in:** Is group membership sufficient consent for the bot to DM a player, or do we need an explicit `/optin` first?
- **UPI:** Static per-user UPI ID stored on the profile, or per-payment generated link with amount pre-filled?

## Status — Shipped on Master (2026-06-18)

**Tier 1 — done:**
- ✅ `User.phone` field (E.164, indexed, unique-when-set)
- ✅ `BotEvent` model (`apps/notifications/models.py`) — keyed on `wa_message_id` for idempotency
- ✅ Cloud API webhook + `X-Hub-Signature-256` verification (`apps/notifications/views.py`)
- ✅ Approved `session_rsvp_temp` template (still in Meta — kept around even though we no longer broadcast)
- ✅ Delivery `statuses` webhook handler — surfaces Meta error codes in `BotEvent.payload.errors`
- ✅ Group-share flow: `build_group_invite_text` + `build_group_share_url`; "Share to WhatsApp Group" link on session detail (3-dot menu)
- ✅ `WHATSAPP_BOT_NUMBER` env var, digit-stripped at use site for forgiving formats
- ✅ Inbound parser (`RSVP_PATTERN`) matches case-insensitive `YES <session_id>` / `NO <session_id>` from wa.me deep links, plus bare YES/NO against latest open poll
- ✅ Bot replies (all free, service-window): vote confirmation with switch hint, balance, status, help, "I don't recognise this number" for unknown phones, "I didn't understand 'X'" with echo for unparseable text
- ✅ STATUS / POLL / WHO / COUNT command — current open poll counts + voter lists
- ✅ Activity feed: red X for "no" RSVPs, green check for "yes" (body-text inspection in `_decorate`)

**Out of scope / parked:**
- ⏸ `WhatsAppGroup` model — not built; not needed for admin-paste flow
- ⏸ `whatsapp-web.js` Node bot — explicitly not built. Would unlock bot-posts-in-group but with ban risk + hosting cost. Only revisit if admin-paste friction becomes unworkable.

**Disabled but still in `services.py` as paid escape hatches:**
- `notify_poll_created` — broadcast template DM
- `resend_poll_invite` — non-voters resend with 6h cooldown
- `send_session_reminders` — 24h / morning / 2h reminders (also gated by `WHATSAPP_REMINDER_TEMPLATE` env var being empty)

## What's Next (Post-Pivot Priorities)

1. **Phone-onboarding deep-link** (~15 min) — "I don't recognise this number" reply currently tells users to add their number but doesn't link to the profile-edit page.
2. **`STATUS <session_id>` + `MYVOTE`** (~20 min) — extend the dispatcher; both are tiny additions on existing handlers.
3. **Free reminder system** (~1 hour) — use the `BotEvent` inbound log to find users with an active 24h service window, send them a free text reminder. Covers the engaged subset only — won't ping cold users.
4. **Phone validation on save** — `User.phone` form accepts whatever's typed; the inbound webhook expects E.164 with `+`. Add a `clean_phone` that normalises on save so deep links land on the right user.
5. **`BotEvent` admin filter** — add `list_filter = ('direction', 'action')` so debugging is faster.

## Future / Open Questions

- **Group-post automation.** If admin-paste friction becomes painful, we revisit `whatsapp-web.js` to have the bot post into the group itself. Ban risk + brittleness + persistent-volume hosting cost remain the trade-offs.
- **Payments.** Payment DMs (the original Tier-1.2 idea) are utility conversations and would cost. Cheapest path: include unpaid totals in the bot's reply to `BALANCE` (free, user-initiated — already shipped).
- **Reminders in the group, not in DM.** Admin could paste a "reminder" message into the group same way they pasted the invite. Considered, deferred — adds friction per session.
- **Confirmation reply on RSVP via web app.** Currently only WhatsApp-channel votes get a "Got it" reply (because that's the only place the bot has a side channel). Web votes are silent. Probably fine, but worth flagging if behaviour feels inconsistent.
