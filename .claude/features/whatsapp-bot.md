# WhatsApp Bot — Club Community POC

**Status:** Proposed (not started)
**Owner:** TBD
**Created:** 2026-05-13

## Goal

Run a bot inside the IndCric club's WhatsApp community/groups that talks to the existing Django app — so the group itself becomes a UI layer for RSVPs, payments, balances, and expense tracking. Cut down the manual "who's coming / who paid" chase that currently happens in chat.

## Constraints & Assumptions

- Bot must operate **inside group chats**, not just 1:1 — that rules out plain Meta Cloud API for the core flow.
- Django stays the **source of truth**. Bot is a thin I/O layer that calls Django via authenticated webhooks.
- WhatsApp users map to `User` rows via phone number — a `phone` field must be added to the `User` model first.
- POC tolerates the risk of unofficial-library breakage (WhatsApp Web client updates) and number-ban risk if message volume is spammy.

## Capability Map

| Channel | Capability | Use |
|---|---|---|
| Group message in | Read text, reactions, mentions | RSVP commands, expense entry, score updates |
| Group message out | Text, images, scheduled posts | Session announcements, team sheets, scorecards |
| DM in | Free text or button responses | Balance lookup, payment confirmation, admin commands |
| DM out | Text + media + UPI links | Payment nudges, per-user reminders |

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

## Next Steps

1. **Add `phone` field to `User`** — migration + admin field. Unique, indexed, nullable for existing users.
2. **Add `WhatsAppGroup` model** — maps a sub-group's `wa_group_id` to a club audience. Admin-managed.
3. **Create `BotEvent` model** — log every inbound/outbound message with WhatsApp message ID, user, action, timestamp. Audit + idempotency anchor.
4. **Stand up Node bot locally** — `whatsapp-web.js` POC, log inbound messages from a single test sub-group. ~2 hours.
5. **Build first webhook**: `POST /api/bot/rsvp/` accepting `{phone, session_id, choice, wa_message_id}` → writes `Vote` via `get_or_create`. Token-auth via `BOT_WEBHOOK_TOKEN`.
6. **Wire end-to-end Tier 1.1 (RSVP)** — bot posts a session in the pilot sub-group, reads replies, calls webhook, confirms back in group.
7. **Decide hosting + bot number** before Tier 1.2/1.3 (payment DMs need stable outbound).
