# Kural's Feature Plan

## Context: How the App Works Today

The app is split into sub-apps under `apps/`:

| App | Purpose |
|---|---|
| `apps/accounts` | `User` model — has `batting_rating`, `bowling_rating`, `fielding_rating` (0–5 Decimal, currently set manually) |
| `apps/matches` | `Match → Team → Player → Innings → Delivery` — full ball-by-ball scoring engine already built |
| `apps/sessions` | `Session`, `SessionPlayer`, `Attendance` — one session = one cricket week |
| `apps/payments` | `Payment`, `Wallet` — cost splitting |
| `apps/polls` | Availability polls (yes/no per session) |
| `apps/notifications` | WhatsApp bot integration |

### How team splitting works today

When staff open a session detail page they see all "yes" voters in a drag-and-drop team editor.
Each player shows a skill meter powered by three functions in `apps/sessions/views.py`:

- `_combined_rating(u)` — averages `batting_rating + bowling_rating + fielding_rating / 3`
- `_player_skills(u)` — returns `{batting, bowling, rating}` used in the UI

Staff drag players across two teams. The skill meter guides them toward balanced totals.
The split is **manual** — the meter is the guide, not an auto-splitter.

**Our job:** keep the split manual, but make the three skill ratings update automatically
from real match performance instead of being set by hand.

---

## Feature 1 — Auto-Ratings from Session Performance

### Goal

After every session ends, each player's `batting_rating`, `bowling_rating`,
and `fielding_rating` on their `User` row are recalculated from their actual
performance history. When staff open the team editor for the *next* session,
the ratings already reflect recent real form.

### When ratings update

Once per session — not after individual matches within a session.
A session can have multiple matches (Match 1, Match 2, …). We aggregate
all of those before recalculating the rating.

### New model: `PlayerSessionStat` (in `apps/matches/models.py`)

One row per player per session — computed when staff mark the session as
finished.

```
PlayerSessionStat
  session       FK → Session
  user          FK → User
  # Batting
  runs          int
  balls_faced   int
  # Bowling
  wickets       int
  balls_bowled  int   (legal)
  runs_conceded int
  # Fielding
  catches       int
  stumpings     int
  # Meta
  computed_at   DateTimeField (auto_now)

  unique_together: (session, user)
```

### How stats are derived

From the existing `Delivery` ledger via the already-written scoring engine:
- Batting: `batting_card(innings)` → sum runs + balls across all matches in the session
- Bowling: `bowling_card(innings)` → sum wickets + balls + runs across all innings
- Fielding: filter `Delivery` rows where `fielder = player` and
  `dismissal_type in ('caught', 'stumped')` across all session matches

### Rating formula (weighted rolling average, all sessions played)

Uses session recency as a weight across **all sessions the player has ever
attended**. Weight is assigned by rank: most recent session = rank 1
(highest weight), oldest session = rank N (lowest weight).
Weight for rank i = (N − i + 1), so newer sessions count more.

**Batting rating (0–5)**

```
strike_rate = (runs / balls_faced) * 100  # if balls_faced > 0, else 0
batting_raw = strike_rate / 30            # SR 150 → 5.0
batting_raw = clamp(batting_raw, 0, 5)
```

Weighted average of `batting_raw` across **all sessions** the player has attended.
If a player never batted in a session (0 balls faced), that session is skipped
for the batting calculation. If they have no batting history at all → rating = 0.

**Bowling rating (0–5)**

```
economy = (runs_conceded / balls_bowled) * 6   # if bowled > 0, else skip
# Lower economy = better → invert for 0–5 scale
bowling_raw = clamp(6 - economy, 0, 5)         # eco 6 → 0 (awful), eco 1 → 5 (great)
```

Weighted average across **all sessions** where player bowled.
If they have never bowled → bowling_rating = 0.

**Fielding rating (0–5)**

```
fielding_raw = clamp((catches + stumpings) * 1.25, 0, 5)
# 0 catches/stumpings → 0; 4+ → 5
```

Weighted average across **all sessions** where player was in a match.
If they have no fielding stats at all → fielding_rating = 0.

### Where the calculation runs

New function `compute_session_ratings(session)` in a new file
`apps/matches/rating_engine.py`:

1. For each match in the session, call `batting_card()` and `bowling_card()`
   from the existing `scoring.py`
2. Aggregate into `PlayerSessionStat` rows (upsert)
3. For each user who appeared, fetch **all** their `PlayerSessionStat` rows
   (ordered newest first)
4. Apply the weighted average formula (rank-based weights across all sessions)
5. Write back to `User.batting_rating`, `User.bowling_rating`,
   `User.fielding_rating` — set to 0 if no history exists for that skill
6. Wrap everything in `transaction.atomic()`

### How it is triggered

**Staff button on session detail page** — "Finalise session & update ratings"
(staff-only, one-time per session). This calls `compute_session_ratings(session)`.

A management command `update_ratings --session <id>` will also exist for
backfilling or manual reruns.

### No change to team-splitting UI

The team editor in `session_detail.html` uses the three ratings as-is.
Because the ratings are now auto-kept up to date, the existing UI shows
accurate skill meters with zero extra work.

---

## Feature 2 — Drinks Rotation

### Goal

Fairly rotate who pays for drinks each session. Two tracks run in parallel:
- **Alcohol track** — for players who drink alcohol
- **Non-alcohol track** — for all other players (including non-drinkers who
  join the soft-drinks rotation)

New players get a **5-session grace period** before entering any rotation.

### New field: `User.drink_preference`

```python
DRINK_CHOICES = [
    ('alcohol',     'Alcohol'),
    ('non_alcohol', 'Non-alcoholic / Soft drinks'),
]
drink_preference = CharField(max_length=15, choices=DRINK_CHOICES, default='non_alcohol')
```

Players who don't drink join the non-alcohol track by default.

### Eligibility rule

A player is eligible for a rotation track when:
1. They have attended **≥ 5 sessions** (`Attendance.attended = True`)
2. They are **attending the current session** (voted yes and confirmed present)

### New model: `DrinkRound` (in `apps/payments/models.py`)

```
DrinkRound
  session       FK → Session
  payer         FK → User
  drink_type    CharField  choices: 'alcohol' | 'non_alcohol'
  recorded_by   FK → User (staff who confirmed it)
  recorded_at   DateTimeField (auto_now_add)

  unique_together: (session, drink_type)   ← one payer per type per session
```

### Next-payer algorithm

For each drink type at a given session:

1. Get all attending, eligible players for that track
2. For each, find their last `DrinkRound` date (null if they never paid)
3. Sort ascending by last-paid date (never paid → treated as infinitely old)
4. The first person in that list is the suggested payer

Tiebreaker: alphabetical by username.

### UI on session detail page

A "Drinks" card (staff-only) shows:
- **Alcohol payer:** `<name>` (last paid: `<date>` or "never")
- **Non-alcohol payer:** `<name>` (last paid: `<date>` or "never")
- A "Confirm" button per track — clicking saves the `DrinkRound` row
- Staff can pick a different person from a dropdown before confirming

This card only appears once the attendance for the session has been confirmed.

### Drink history on the user dashboard / profile page

On each player's own profile page (and the manage-users profile view for staff),
add a **"Drinks paid"** section showing a chronological list of sessions where
the player paid for drinks:

| Date | Session | Track |
|---|---|---|
| 12 May 2026 | Tuesday Evening Session | Alcohol |
| 28 Apr 2026 | Tuesday Evening Session | Non-alcohol |

This is derived from `DrinkRound.objects.filter(payer=user).order_by('-session__date')`.
If the list is empty, show: *"No drink rounds recorded yet."*

### Grace period display

On the player profile page, if a player has < 5 attended sessions, show:
"Drinks rotation: joins after X more sessions"

---

## Implementation Order

1. `PlayerSessionStat` model + migration
2. `rating_engine.py` — `compute_session_ratings(session)` function
3. Staff "Finalise & update ratings" button on session detail
4. Management command for backfilling
5. `DrinkRound` model + migration + `User.drink_preference` field
6. Next-payer algorithm function
7. Drinks card on session detail (staff view)
8. Grace period display on profile page
9. Drink history list on user profile/dashboard page
