# User History — Games, Payments, Wallet Ledger

**Status:** Spec only — no code yet
**Owner:** bhanu
**Created:** 2026-05-28

## Goal

Surface each user's full activity history in three focused views:

1. **Games played** — every session they attended, with team, result, and personal stats
2. **Payments** — every per-session payment they made, with amount, method, and status
3. **Wallet ledger** — every wallet movement (top-up, session debit, refund, staff adjustment) with running balance

The data already exists in the database; this feature is about giving it a home in the UI.

## Why now

Triggered by the wallet bug found on 2026-05-28: the manage-users page showed Gill's wallet as €100 even after a €20 session debit, because the table read `Wallet.objects.first()` instead of `Sum('amount')`. Fixing the read surface revealed that **we already maintain a ledger** — we've just never exposed it.

When wallet balances and "owed" amounts move silently in the background, the only path users have today to question a balance is to ask staff. Once they can see "your wallet was €100, you played on 12 May (€20 debit), you topped up €30 on 20 May, current balance €110" the system explains itself.

## What data already exists

| Model | Rows per user | What it tells us |
|---|---|---|
| `apps.sessions.SessionPlayer` | One per (user, session) | Did the user join the session roster |
| `apps.sessions.Attendance` | One per SessionPlayer | Did they actually show up (`attended=True`) |
| `apps.matches.Player` | One per (user, team, match) | Which team they were on, did they play, role |
| `apps.payments.Payment` | One per (user, session) | Amount owed, status (`pending|paid`), method (`wallet|cash`) |
| `apps.payments.Wallet` | Many per user (ledger) | Each row is a delta: top-up, debit, refund, adjustment. `status` field tags the kind. Sum across rows = current balance. |

### `Wallet.status` taxonomy (already in use)

| Value | Meaning | Sign | Created by |
|---|---|---|---|
| `paid` | Debit triggered by marking a Payment paid | Negative | manage-payments save flow |
| `refund` | Reversal when staff un-pays a wallet-settled payment | Positive | manage-payments save flow |
| `adjustment` | Staff overrode the balance via edit-user form | Either | manage-users edit flow |
| `pending` *(legacy)* | Initial top-up rows from before the ledger was clarified | Positive | manual / migrate |

(We may want a new `topup` status going forward — see Decisions Pending.)

## Design — three tabs, one page

### Where it lives

- **Player's own view:** `/profile/` already has a stats card. Add a tabbed history strip below it.
- **Staff view of any user:** `/profile/<username>/` — same template, same tabs. Staff sees everyone's history; players see only their own.

### Tab layout

```
┌─ Profile header (avatar, name, role, ratings) ─┐
└────────────────────────────────────────────────┘
┌─ Stats card (matches played, runs, wickets) ──┐
└────────────────────────────────────────────────┘
┌── [Games] [Payments] [Wallet] ───────────────┐
│                                              │
│  (selected tab content)                      │
│                                              │
└──────────────────────────────────────────────┘
```

Tabs use HTMX `hx-get` + a `?tab=games|payments|wallet` query param so each tab loads its own partial without a full reload.

### Tab 1 — Games

A reverse-chronological list of sessions the user attended. One row per session.

| Column | Source | Notes |
|---|---|---|
| Date | `Session.date` | Day + month, formatted |
| Session name | `Session.name` | Links to `/session/<id>/` |
| Venue | `Session.location` | Small text |
| Team | `Player.team.name` for the matching Match | `—` if no match created |
| Result | `Match.result` (future field) | Show only when scoring lands |

Filter chips: `All` · `Played` · `Voted no` — based on `SessionPlayer` + `Vote` cross-reference.

### Tab 2 — Payments

Reverse-chronological list of `Payment` rows.

| Column | Source | Notes |
|---|---|---|
| Date | `Payment.date` | Day + month |
| Session | `Payment.session.name` | Links to session |
| Amount | `Payment.amount` | Right-aligned, monospace |
| Method | `Payment.method` | Badge: `wallet` (pitch) / `cash` (stone) |
| Status | `Payment.status` | Badge: `paid` (green) / `pending` (amber) |

Footer row: totals — total paid, total pending, total via wallet, total via cash.

### Tab 3 — Wallet ledger

Reverse-chronological list of `Wallet` rows with a running balance column.

| Column | Source | Notes |
|---|---|---|
| Date | `Wallet.date` | Day + month |
| Description | Derived from `Wallet.status` and any linked Payment | "Top-up", "Session: <name>", "Refund: <name>", "Staff adjustment" |
| Amount | `Wallet.amount` | Green for positive, red for negative |
| Balance | Running sum | Computed in the view, oldest-first then reversed for display |

Header strip: current balance (big), 30-day delta (small).

Sticky CTA on mobile (staff-only): "Adjust balance" → opens a small form that lets staff enter a new total. Backed by the same `delta = new_total - current_balance → create Wallet(amount=delta, status='adjustment')` logic the edit-user form now uses.

## Why three tabs, not one timeline

Considered a single unified timeline (one feed mixing games + payments + wallet rows). Rejected because:

- **Wallet debits and the matching session payments are the same event from two angles.** Showing both in one feed creates visible duplicates (`Session X — paid €20` next to `Wallet — €20 debit for Session X`).
- **Different questions, different scans.** "When did I play last?" is a game tab. "Why is my balance €80?" is a wallet tab. A mixed feed forces every reader to filter mentally.
- **Mobile.** Each tab fits 5–10 rows on a phone screen; a mixed feed is twice as long and harder to scroll.

A "Money" tab (Payments + Wallet collapsed with deduplication) is the fallback if three tabs feel like too much navigation. It needs a join rule (a wallet `paid` row + the Payment it settled count as one event) which adds template complexity.

## Implementation plan

### Step 1 — View + URL

- New view `apps.accounts.views.profile_history_view(request, username, tab)` that:
  - Loads the target user (or `request.user` if username is the same)
  - Permission check: staff or self
  - Dispatches on `tab`:
    - `games` → returns `_history_games.html` partial with session + match list
    - `payments` → returns `_history_payments.html` partial with Payment rows
    - `wallet` → returns `_history_wallet.html` partial with Wallet rows + running balance
- URL: `path('profile/<str:username>/history/<str:tab>/', views.profile_history_view, name='profile_history')`

### Step 2 — Templates

| Path | Purpose |
|---|---|
| `cric/templates/cric/pages/profile.html` | Add tabs strip + `hx-get` swap target |
| `cric/templates/cric/partials/_history_tabs.html` | The tab buttons (Alpine-driven active state) |
| `cric/templates/cric/partials/_history_games.html` | Tab 1 |
| `cric/templates/cric/partials/_history_payments.html` | Tab 2 |
| `cric/templates/cric/partials/_history_wallet.html` | Tab 3 + running balance computation |

### Step 3 — Wallet history aggregation

Running balance is computed in Python rather than via window functions to keep the SQLite/Postgres compat surface small.

```python
rows = list(Wallet.objects.filter(user=u).order_by('date', 'id'))
running = Decimal('0')
for r in rows:
    running += r.amount
    r.balance = running   # in-memory attribute for the template
rows.reverse()  # newest first for display
```

For the "Description" column, look up the linked Payment when status in `('paid', 'refund')`:

```python
# Pair Wallet rows to Payment rows by (user, abs(amount), close date).
# Brittle — the long-term fix is a `payment` FK on Wallet, see below.
```

### Step 4 — Staff "Adjust balance" inline form

- Staff sees a small form in the Wallet tab header
- POST creates a `Wallet(amount=delta, status='adjustment')` row, same logic as `edit_user_view`
- Refresh just the tab partial via HTMX, not the whole page

### Step 5 — Filters and totals

- Games tab: chip filter `All` / `Played` / `Voted no`
- Payments tab: chip filter `All` / `Paid` / `Pending`; footer totals
- Wallet tab: chip filter `All` / `Debits` / `Credits` / `Adjustments`

## Decisions pending

1. **Should we add a FK from `Wallet` to `Payment`?**
   Right now the link is implicit (same user, same amount, same date). Adding `payment = models.ForeignKey('payments.Payment', null=True, blank=True, on_delete=models.SET_NULL)` would make the "Description" column trivial and let the Money-tab fallback work cleanly. Migration is cheap (nullable FK on a small table). **Recommend yes.**

2. **Should we add a `topup` status to `Wallet`?**
   Existing top-ups use `status='pending'` which is confusing — it suggests the row is unsettled. A `topup` value cleans this up. Migration via `RunPython` to rename old rows. **Recommend yes** (small).

3. **Who can see whose history?**
   - Self: yes
   - Staff: all users — needed for support / dispute resolution
   - Peer: probably not, even for the Games tab — confirm with team. **Default to: self + staff only.**

4. **Pagination?**
   At ~1 session/week × 1 year = 52 rows per tab. Fine without pagination for v1. Add later if the club scales or if old players accumulate hundreds of rows.

5. **Export to CSV?**
   Useful for end-of-year accounting. Not blocking v1; flag for v1.1.

## Out of scope

- Per-session batting/bowling stat history (already on the profile via `PlayerProfile` aggregate; per-match stats need a separate `PlayerMatchStats` model which is its own feature)
- Wallet transfer between users (not currently a feature)
- Expense-split history (separate feature in [.claude/skills/expense-splitting/SKILL.md](../skills/expense-splitting/SKILL.md))

## Next steps when we pick this up

1. Confirm the three decisions above
2. Add `payment` FK + `topup` status migration if approved
3. Implement Step 1 (view + URL) — the data layer
4. Implement Steps 2–3 (templates + balance aggregation) — the visible layer
5. Implement Step 4 (staff adjust) — replaces the wallet edit on the manage-users form
6. Implement Step 5 (filters + totals) — polish
