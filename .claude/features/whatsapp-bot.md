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

- Which group(s) does the bot join? One pilot group, or the full community from day one?
- Number choice: dedicated SIM/eSIM for the bot, or a Twilio-style virtual number? Affects ban-risk recovery.
- Do we need an opt-in flow per user (privacy), or is membership in the group sufficient consent?
- UPI link generation: static per-user UPI ID, or generated per-payment with amount pre-filled?

## Next Steps

1. **Add `phone` field to `User`** — migration + admin field. Unique, indexed, nullable for existing users.
2. **Create `BotEvent` model** — log every inbound/outbound message with WhatsApp message ID, user, action, timestamp. Audit + idempotency anchor.
3. **Stand up Node bot locally** — `whatsapp-web.js` POC, log inbound group messages for a test group. ~2 hours.
4. **Build first webhook**: `POST /api/bot/rsvp/` accepting `{phone, session_id, choice, wa_message_id}` → writes `Vote` via `get_or_create`. Token-auth.
5. **Wire end-to-end Tier 1.1 (RSVP)** — bot posts a session, reads replies, calls webhook, confirms back in group.
6. **Decide hosting + bot number** before Tier 1.2/1.3 (payment DMs need stable outbound).
