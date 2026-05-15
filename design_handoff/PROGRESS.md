# IndCric Design Overhaul — Progress & Handoff

Single source of truth for **where the design refresh stands and what to do next**.
Update this file at the end of every working session so any machine (or future Claude session) can pick up without re-discovery.

Last updated: **2026-05-15**
Last commit: **`ed1a74a` — Add design overhaul progress tracker for handoff between machines**
Branch: **`master`** (synced with `origin/master`)

---

## How to resume on another machine

1. `git pull` to fetch commit `a0f9412` (push first from the source machine if not pushed yet).
2. Activate venv: `source .venv/Scripts/activate` (bash) or `.venv\Scripts\activate` (PowerShell).
3. Run `docker-compose up -d` (Postgres) and `python manage.py runserver`.
4. Open this file (`design_handoff/PROGRESS.md`) and pick the next pending slice below.
5. Tell Claude:
   > "Read `design_handoff/PROGRESS.md`. We're picking up at the next pending slice — start <slice name>."

---

## Token sources — single-source-of-truth map

**Before touching any class in [templates/base.html](../templates/base.html), check the row here.** If the change you're making doesn't match the listed spec, either fix the template back to spec or update this table with the reason for the drift.

The "Spec" column lists exact pixel values from the design handoff. The "Implements" column is the resulting `@apply` chain in base.html.

| CSS class | Spec source | Spec values | Implements |
|---|---|---|---|
| `.card`        | [README.md:106](README.md#L106) | 16 px radius, 1 px stone-100 border, shadow-sm | `rounded-2xl border border-stone-100 shadow-sm` |
| `.btn` (base + `.btn-md`) | [README.md:105](README.md#L105) · [preview/_card.css:54](preview/_card.css#L54) | 8 px radius, 13 px / 500 weight, 7×14 padding, 6 px gap | `gap-1.5 font-medium text-[13px] rounded-lg` + `.btn-md: px-3.5 py-[7px]` |
| `.btn-sm`      | [preview/_card.css:76](preview/_card.css#L76) | 5×10, 12 px, 7 px radius | `px-2.5 py-1 text-xs rounded-[7px]` |
| `.btn-lg`      | [preview/_card.css:77](preview/_card.css#L77) | 9×18, 13 px, 9 px radius | `px-[18px] py-[9px] rounded-[9px]` |
| `.badge`       | [README.md:107](README.md#L107) | 11 px / 600 weight, full pill, 100-bg / 800-fg | `text-[11px] font-semibold rounded-full px-2.5 py-0.5` |
| `.role-badge`  | [README.md:108](README.md#L108) | 11 px outline pill, role-tinted | `text-[11px] font-semibold border rounded-full` + tint variants |
| `.form-input`  | [README.md:113](README.md#L113) | 10 px radius, 13 px text, stone-200 border, 2 px pitch-500 focus shadow | `rounded-[10px] text-[13px] border-stone-200 focus:ring-2 focus:ring-pitch-500` |
| `.stat-tile`   | [README.md:112](README.md#L112) | 10 px radius, soft 50-bg / 100-border | `rounded-[10px] border` + per-tint variants |
| `.stat-col`    | [README.md:111](README.md#L111) | mono 9 px label, 22-24 px tnum numeric, 1 px stone-100 rule between | `border-l border-stone-100 first:border-l-0` + 22 px num |
| `.player-chip` | [README.md:110](README.md#L110) | 8 px radius, hairline border (role-tinted) | `rounded-lg border-stone-100` · **role-tint still TODO** |
| `.alert`       | [README.md:114](README.md#L114) | 10 px radius, 50-bg / 100-border / 800-fg | `rounded-[10px] border p-4` + tint variants |
| `.skill-bar` / `.skill-seg` | [ui_kits/indcric_web/Primitives.jsx:152](ui_kits/indcric_web/Primitives.jsx#L152) | 5 segments × 16×4 px, 2 px radius, 4 px gap, stone-800 fill / stone-100 empty | `.skill-bar gap-1` + `.skill-seg w-4 h-1 rounded-sm` |
| `.eyebrow`     | [colors_and_type.css:138, 223-229](colors_and_type.css#L138) + [DESIGN_SYSTEM.md:101-103](DESIGN_SYSTEM.md#L101) | 11 px UPPERCASE, 700 weight, **0.05 em** tracking, stone-500 | `text-[11px] font-bold uppercase tracking-[0.05em] text-stone-500` |
| `.micro-label` | [JSX SectionHeader Primitives.jsx:74-83](ui_kits/indcric_web/SessionDetailScreen.jsx#L74) | mono 9-10 px UPPERCASE, 0.08 em tracking, stone-400 | `font-mono text-[9px] uppercase tracking-[0.08em] text-stone-400` |
| `h1`           | [colors_and_type.css:195-201](colors_and_type.css#L195) | 24 px / 700, line-height 1.3, tracking **-0.015 em**, stone-900 | `text-2xl font-bold text-stone-900 leading-snug tracking-[-0.015em]` |
| `h2`           | [colors_and_type.css:203-208](colors_and_type.css#L203) | 18 px / 700, line-height 1.3, stone-800 | `text-lg font-bold text-stone-800 leading-snug` |
| `h3`           | [colors_and_type.css:210-214](colors_and_type.css#L210) | 16 px / 600, stone-800 | `text-base font-semibold text-stone-800` |
| `body` (font)  | [colors_and_type.css:112-114, 183-193](colors_and_type.css#L112) | Inter, 16 px, line-height 1.5, antialiased | `<link>` Inter 400-800 + `font-sans bg-stone-50 antialiased` in body |
| `.card-accent` | [README.md:106](README.md#L106) (last line) | 4 px top accent bar | `h-1 rounded-t-2xl` + per-tone variants |
| `.date-pill`   | preview/component-session-card.html | inline icon + DD MMM, 12 px rounded pill, pitch-50 / pitch-800 | `rounded-xl px-3 py-1.5 text-xs font-semibold bg-pitch-50 text-pitch-800` |
| `.vote-bar`    | [Primitives.jsx:181](ui_kits/indcric_web/Primitives.jsx#L181) | 6 px height, full radius, stone-100 track, emerald-500 fill, 500 ms transition | `h-2 rounded-full bg-stone-100 overflow-hidden` |

**Known partial drifts (acceptable for now):**
- `.player-chip` border is plain `stone-100` — JSX/spec wants role-tinted hairline (sky / red / purple / stone). Will be addressed when player chip becomes role-aware (needs a `role=` arg on the partial).
- `.form-input` padding is `px-4 py-2.5` (16×10) vs README hint of 14×10 — 2 px wider; not visually disruptive.
- `.eyebrow` tracking is `0.08em` (matches micro-label) vs DESIGN_SYSTEM hint of `0.05em` — chose consistency with micro-label.

---

## Phase plan at a glance

| Phase | Slice | Status |
|---|---|---|
| 1 | Foundation (tokens, partials, assets) | **Done** |
| 2 | Login screen refresh | **Done** |
| 2 | Dashboard refresh | **Done** |
| 2 | Sign-up screen refresh | **Done (uncommitted)** |
| 2 | Dashboard auth-tier gating | **Done (uncommitted)** |
| 2 | Session detail refresh | **Done (uncommitted)** |
| 2 | Profile refresh | **Done (uncommitted)** |
| 2 | Payments refresh ("By match" / "Who owes whom" tabs) | **Pending** |
| 3 | Wallet transaction history (new) | **Pending** |
| 3 | Team balance / snake-draft (new) | **Pending** |
| 3 | Match result with scorecards (refresh skeleton) | **Pending** |
| 3 | Notifications tabbed feed (new) | **Pending** |
| 3 | Onboarding 3-step refresh | **Pending** |
| 3 | Mobile bottom nav (last) | **Pending** |

---

## What's done — Phase 1 (Foundation)

### Brand assets
- [static/icons/logo-mark.png](../static/icons/logo-mark.png) — canonical comet-ball monogram, copied from `design_handoff/assets/logo-mark.png`.
- `ball.png` and `bat.png` already present in `static/icons/`.

### Tokens & utility classes — [templates/base.html](../templates/base.html)
Added (all additive, no existing class was modified):
- `.eyebrow`, `.micro-label`, `.section-eyebrow`, `.section-eyebrow-bar(-past)` — section labels.
- `.stat-tile`, `.stat-tile-{sky,red,emerald,amber,pitch,stone}`, `.stat-tile-num` — soft-tinted KPI cells.
- `.stat-col`, `.stat-col-num` — typographic column with mono label + tnum numeric, separated by 1px stone-100 rule.
- `.card-accent`, `.card-accent-{pitch,stone,amber,red,sky}` — 4 px top accent bars.
- `.date-pill`, `.date-pill-past` — calendar-icon + DD MMM pill.
- `.alert`, `.alert-{info,success,warn,error}-box` — alert boxes per design spec.
- `.role-badge`, `.role-badge-{bat,ball,allr,keeper}` — outline pill with role tint.
- `.skill-bar`, `.skill-seg`, `.skill-seg-fill` — 5-segment skill rating with half-step support.

### Template tag — [apps/accounts/templatetags/custom_filters.py:13-37](../apps/accounts/templatetags/custom_filters.py)
- `role_emoji` — maps `batsman/bowler/allrounder/fielding/keeper` to their canonical emoji glyphs.

### Reusable partials — [templates/_components/](../templates/_components/)
Eleven self-contained `{% include %}` partials. All accept named args via `{% include "_components/<x>.html" with arg=val %}`. All pass compile + render smoke tests.

| Partial | Purpose |
|---|---|
| [button.html](../templates/_components/button.html) | All 6 variants × 4 sizes, optional leading icon, optional `url=` (renders `<a>` vs `<button>`) |
| [badge.html](../templates/_components/badge.html) | Pill badge with 7 tone variants |
| [role_badge.html](../templates/_components/role_badge.html) | Outline pill with role tint + emoji glyph, `compact=True` for icon-only |
| [eyebrow.html](../templates/_components/eyebrow.html) | Section header with accent bar + UPPERCASE label, `past=True` for muted variant |
| [date_pill.html](../templates/_components/date_pill.html) | Calendar-icon + date, `past=True` for stone-tinted variant |
| [alert.html](../templates/_components/alert.html) | Info / success / warn / error alert box |
| [rating_bar.html](../templates/_components/rating_bar.html) | 5-segment skill bar rounded to halves |
| [stat_column.html](../templates/_components/stat_column.html) | Mono UPPERCASE label + colour dot + tnum numeric, `first=True` kills left border |
| [stat_tile.html](../templates/_components/stat_tile.html) | Soft-tinted KPI tile with label, value, optional delta |
| [player_chip.html](../templates/_components/player_chip.html) | Avatar + name + optional role glyph + optional captain pip |
| [session_card.html](../templates/_components/session_card.html) | Session card with date pill, name, location/time, optional poll bar, past-state styling |

**Gotcha discovered:** Django template variables cannot start with underscore. All `{% with _name=... %}` got renamed (e.g. `bvariant`, `rkey`, `rv`, `dotc`, `tval`, `av`).

---

## What's done — Phase 2 (Login)

### Refreshed — [templates/account/login.html](../templates/account/login.html)
- Replaced homemade cricket-bat SVG with canonical `logo-mark.png` on a soft white tile (dark hero panel) and on a `ring-stone-100` white tile (mobile-only).
- Eyebrow pill ("CRICKET CLUB MANAGER") now `font-mono text-[11px] uppercase tracking-[0.08em]`.
- Hero heading dropped from `font-extrabold` (800) → `font-bold` (700) per spec.
- Hero subtitle colour shifted from `pitch-400` → `pitch-300`.
- Feature list copy updated to match JSX: "Session payments & settlement", "Attendance polls & match history".
- Bottom copyright is now mono-uppercase: `© 2026 IndCric · Built for the club`.
- Non-field-errors block now uses `_components/alert.html` with `variant="error"`.
- Removed dead no-op `{% for item in "0,1,2,3"|make_list %}{% endfor %}` loop.

**Form behaviour unchanged.** All field rendering, errors, `showPass` toggle, CSRF, redirect_field_value, "Remember me", and forgot-password / signup links are byte-identical to before.

### Verification done
- `GET /accounts/login/` → 200, 28 KB.
- `/static/icons/logo-mark.png` → 200.
- All key markers present in rendered HTML.

---

## What's done — Phase 2 (Dashboard)

### View — [apps/sessions/views.py](../apps/sessions/views.py) (`home`)
New context values:
- `next_session` = first upcoming session.
- `next_session_votes` = vote counts for `next_session` (yes/no/total/yes_percentage), or `None`.
- `sessions_30d` = count of sessions in last 30 days.
- `outstanding_total` = sum of `Payment.amount` where `user=request.user, status='pending'` (Decimal('0') for anonymous).
- `active_members` = count of users with `is_active=True`.

### Template — [templates/home.html](../templates/home.html) (full rewrite)
- Welcome row with H1 + 👋 + staff-only **New Session** button.
- **Snapshot strip** (`grid-cols-[1.4fr_1fr_1fr_1fr]` on lg+):
  - Next-up hero card with `card-accent-pitch`, mono "Next up · {date}", session name + meta, in/out vote summary, "Open →" affordance.
  - Three stat-column cards using `_components/stat_column.html` (pitch / amber / sky dots).
- **Shortcut row** — staff-only "Settle payments" + "Attendance" + universal "Past sessions" anchor (`#previous-sessions`).
- Section eyebrows use `_components/eyebrow.html` (with `past=True` for previous).
- Both card grids use `_components/session_card.html` — single source of truth.

### Verification done
- `GET /` (authed) → 200, 29 KB, all markers present.
- `GET /` (anon) → 200, 19 KB, degrades cleanly.

---

## What's done — Phase 2 (Sign-up)

### Shared hero — [templates/account/_entrance_hero.html](../templates/account/_entrance_hero.html) (new)
- Login's dark-hero panel lifted verbatim into a reusable partial: pitch-950 background, cricket-ground watermark SVG, logo on white tile, mono pill, hero heading, subtitle, 4-item feature list, mono footer.
- Single brand panel — same copy shown on login and signup. Verbatim per spec.

### Refreshed — [templates/account/login.html](../templates/account/login.html)
- Inline hero block replaced with `{% include "account/_entrance_hero.html" %}`.
- Right panel byte-identical to prior commit; only the LEFT changed (from inlined HTML to include).

### Refreshed — [templates/account/signup.html](../templates/account/signup.html)
- Old hero (steps/numbered list + amber pulse) removed in favour of the shared hero.
- Right panel rebuilt to match login's design pattern: identical mobile-logo treatment, identical heading/subtitle typography, `_components/alert.html` for non-field errors, identical input/eye-toggle markup, identical submit button + arrow icon.
- Subtitle copy: "Join your club's session board".
- Bottom link: "Already a member? Sign in →" → `account_login`.
- Form behaviour unchanged. Action still posts to `account_signup` with `?next=profile-onboarding`. Username + email + password1 + password2 fields preserved with autocomplete + autofocus.

**Verify:** Template compile passes for all 3 (`account/_entrance_hero.html`, `account/login.html`, `account/signup.html`). Smoke render via test client blocked by unmigrated SQLite (no `django_site` table on this PC), not a template issue.

---

## What's done — Phase 2 (Dashboard auth-tier gating)

User-requested addition (2026-05-15): the dashboard exposes different surfaces to anonymous / non-staff / staff viewers.

### Template — [templates/home.html](../templates/home.html)
- **Anonymous** — snapshot strip + shortcuts hidden, but upcoming + previous session lists ARE shown in a "locked" state. Each `session_card.html` accepts a new `locked=True` arg: card displays a mono "Locked" pill where the staff delete affordance normally sits, and the card's link redirects to `/accounts/login/?next=<session_detail_url>` instead of the session page. Top of the page shows a "What's on at the club" header with inline Sign In + Create-account CTAs.
- **Non-staff (authenticated)** — snapshot strip collapses to 2 cards: Next-up (1.4fr) + Outstanding (1fr, the user's own pending balance). Sessions·30d and Active-members stat columns are hidden.
- **Staff** — full strip as before (Next-up + 3 stats) and full shortcut row (Settle payments + Attendance + Past sessions).
- Settle payments and Attendance shortcuts were already staff-only and remain so.
- Grid `lg:grid-cols-*` adapts based on `{% if user.is_staff %}`.

**Verify:** Template compile passes.

## What's done — Phase 2 (Session detail)

### Refreshed — [cric/templates/cric/pages/session_detail.html](../cric/templates/cric/pages/session_detail.html)
Surgical refactor — all existing forms, IDs, and the drag-and-drop team editor JS are untouched. Only the visual chrome changed.

**New chrome (top of page, replacing the old "SESSION HEADER CARD"):**
- **Hero card** — `bg-gradient-to-r from-pitch-800 to-pitch-600` gradient strip (h-14) at the top, with a 14×14 white "date tile" floating over the gradient (rounded-2xl, shadow-md, big `j` numeral over mono `M Y` micro-label). Right of the date: poll-status badge (Open / Closed) + Confirmed pill. Below: session name in `text-xl font-semibold -tracking-[0.015em]`, then a meta row with location · time · organiser glyphs.
- **Cost split card** — `_components/eyebrow.html` header + a 3-column row of `_components/stat_column.html` (matching `SessionDetailScreen.jsx:55-58` — typographic columns with leading colored dots, not soft-tinted tiles): Hall fee (stone dot), Voted in (sky dot, yes-vote count), Per player (pitch dot). Per-player tile falls back to "—" while `cost_per_person` is null. When yes-votes > 0 but attendance not yet confirmed, label switches to "Per player (est.)" and value is the live cost ÷ yes-votes preview.
- **Going card** (bottom) — `_components/eyebrow.html` header with confirmed count in mono micro-label on the right, flex-wrap body of `_components/player_chip.html` for each `yes_voter` with `show_role=True`. Only renders when `yes_voters` is non-empty.

**Preserved verbatim:**
- 1/3 + 2/3 split for poll + matches (works well on desktop; not worth flattening).
- Full poll voting UI (I'm in / Can't make it / withdraw flow, expandable voter lists, vote bar).
- Admin controls card (Close/Reopen poll, Delete session) — staff-only.
- Match cards' summary + scoring form (drag-down "Show players" + "Score").
- **Team editor** — every `id="..."` consumed by the inline JS (drag-drop, shuffle, captain badge, save) is unchanged. Verified 18 hook IDs present after refactor.
- All `{% csrf_token %}`, form actions, and named URLs.

**Single small markup change inside match cards:** the in-card team player list (the `x-show="open"` panel) now uses `_components/player_chip.html` instead of the hand-rolled avatar+name divs. Captain pip handled by branching on `team.captain.id == player.user.id`.

**Known divergence from the JSX reference:** `SessionDetailScreen.jsx` (lines 94-97) shows a standalone side-by-side `TeamCard A` + `TeamCard B` block at the top level — but the JSX assumes one fixed pair of teams per session. The production model allows **multiple `Match` rows per `Session`**, each with its own pair of `Team`s. We therefore left team rosters inside match cards (collapsible behind "Show players") rather than promoting one pair to top-level. The visual treatment of each team (pitch dot for Team 1, amber dot for Team 2, captain pip, role glyphs) matches the JSX `TeamCard` spec inside that match-card context. If/when the data model is constrained to one match per session, the top-level pair from the JSX can be lifted in.

**Verify:** template compiles. Test client `GET /session/{id}/` returns 200; all 18 JS hook IDs present; gradient + cost-split tiles + organised-by row all render. Going card gated on `yes_voters`.

## What's done — Phase 2 (Profile)

### Refreshed — [cric/templates/cric/pages/profile.html](../cric/templates/cric/pages/profile.html)
Full rewrite. Both view-mode and edit-mode preserve all form fields, action URLs, and behaviour — only visual chrome changed.

**View mode:**
- **Identity card** — `bg-gradient-to-r from-pitch-800 to-pitch-600` (h-16) gradient strip. 60×60 amber-500 avatar disc with `ring-4 ring-amber-400/30` and `shadow-lg`, overlapping the gradient (`-mt-7`). Display name in `text-lg font-semibold -tracking-[0.01em]`, mono `@username` underneath. `_components/role_badge.html` + amber "Staff" badge inline. Mail icon + email + (optional) phone glyph row below.
- **Skill Ratings card** — `_components/eyebrow.html` section header. Three rows in `grid-cols-[1fr_auto_auto]`: emoji + label · 5-segment `_components/rating_bar.html` · mono tnum value. The continuous `.rating-bar` from the old page is gone; the new partial renders fixed-width 5-segment bars rounded to halves.
- **Career Stats card** — `_components/eyebrow.html` section header + 5-up grid of `_components/stat_tile.html` (pitch / sky / red / amber / stone tints for Matches / Runs / Wickets / Catches / Stumpings). Rendered only when `user.playerprofile` exists.

**Edit mode:**
- Light visual refresh: eyebrow header on the form card, skill-rating heading now reads "Skill Ratings — 0.0 — 5.0" with a mono micro-label suffix.
- Role radio cards, number inputs, Save/Cancel buttons, and form behaviour unchanged. `step="0.5"` now matches the rating-bar's half-step rounding.

**Verify:** template compiles. `/profile/` renders 200 with gradient + ring-amber avatar + role_badge + 5-segment skill-bars + stat tiles. `/profile/?edit=True` renders 200 with `id_batting_rating` / `id_bowling_rating` / `id_fielding_rating` inputs present.

### D. Payments — [cric/templates/cric/pages/payments.html](../cric/templates/cric/pages/payments.html)
**Goal:** Add tabbed layout — "By match" + "Who owes whom" settlement plan.

**Reference:** [design_handoff/ui_kits/indcric_web/PaymentsScreen.jsx](ui_kits/indcric_web/PaymentsScreen.jsx).

**Plan:**
1. Use HTMX-driven tabs — two buttons that swap into a target div via `hx-get` + `hx-target`.
2. **Tab 1 "By match"** — existing list view, but cards instead of the table.
3. **Tab 2 "Who owes whom"** — new settlement-plan view. View must compute net balances per user, then run a debt-simplification (greedy match: biggest creditor ↔ biggest debtor, repeat).
4. Touch points: `apps/sessions/views.py:payments_view` (or split into `payments_by_match_view` + `payments_settlement_view`).

**Skill file:** [.claude/skills/payments-wallet/SKILL.md](../.claude/skills/payments-wallet/SKILL.md) and [.claude/skills/expense-splitting/SKILL.md](../.claude/skills/expense-splitting/SKILL.md) cover the model details before editing.

---

## What's done — Phase 2 (Session detail — pass 2: Team Balance section)

The design handoff was revised mid-flight: `TeamBalanceScreen.jsx` was deleted, and team-balance functionality was moved **into** Session Detail per the new `DESIGN_SYSTEM.md` audience matrix.

### Refreshed — [cric/templates/cric/pages/session_detail.html](../cric/templates/cric/pages/session_detail.html)
- **Going card removed** — yes-voters now live in the Team Balance "Available pool".
- **Team Editor section → Team Balance section.** Header now reads `Team balance · Draft` (mono micro-label, matches `SessionDetailScreen.jsx:142-146`).
- **Skill-gap meter row** between header and slot grid: 3-col grid (Team A meter | gap badge | Team B meter). Badge tints: green `<0.15` Balanced, amber `<0.5` Close, red Uneven. Numbers update live on drag/click.
- **Slot grid layout**: 2-col (no more 3-col with pool sidebar). Pool moved below as a full-width dashed-border container.
- **Slot-row partial** [cric/partials/_team_slot_row.html](../cric/templates/cric/partials/_team_slot_row.html): avatar disc · `username` · mono `role · rating` · 5-segment compact RatingBar · captain pip · swap-to-other (▶) + remove-to-pool (✕) buttons.
- **Pool-chip partial** [cric/partials/_pool_chip.html](../cric/templates/cric/partials/_pool_chip.html): role-tinted pill (sky / red / purple / stone for batsman / bowler / allrounder / default) + `username` + rating mono + `A` / `B` add buttons.
- **Auto-balance** (was random Shuffle): snake-draft — sort all chips by `data-rating` desc, alternate-pick `A B B A A B B A …`. Captain → first player of each team.
- **JS** rewritten: `moveChip()` is the single move primitive used by drag-drop, swap, remove, and A/B buttons; calls `updateHiddenFields()`, `updateMeter()`, `updatePoolDisplay()` on every move. All 18 prior JS hook IDs preserved + 9 new meter/pool IDs added (verified).

### Touched — [apps/sessions/views.py](../apps/sessions/views.py)
- Added `_combined_rating()` helper — average of `batting_rating + bowling_rating + fielding_rating` (each defaulted to `2.5` if None).
- `yes_voters` entries now include `rating` (float). `edit_team1_players` and `edit_team2_players` are now `{'user', 'rating'}` dicts instead of raw `Player` objects.

### Refreshed — [templates/home.html](../templates/home.html) (dashboard cleanup per new audience matrix)
- **Snapshot strip is staff-only.** Non-staff no longer sees Outstanding tile — entire strip is gated behind `user.is_staff`.
- **"Balance teams" shortcut** added for all logged-in users (when `next_session` exists). Links to `#team-editor` anchor on the next session detail.

**Verify:** Template compiles. `/session/2/` returns 200, all 18 original + 9 new JS hook IDs present. `/` (staff) shows the stats strip + Balance teams shortcut. Snake-draft, skill-gap meter, role-tinted pool chips, swap/remove buttons all render.

### Follow-up polish (after first round of user testing)
- **Chip-shape renderer in JS.** Pool chips are `inline-flex` (intentional for horizontal wrap); when Auto-balance / A / B / drag moves them into a team, JS now **rebuilds inner HTML + outer classes** via `renderAsTeamRow()` / `renderAsPoolChip()` so chips become block-level row layout in teams and stack vertically. Added `data-username` + `data-role` to both partials so the renderer has what it needs.
- **Captain pip moved inline with username.** Was sitting in the actions cluster on the right; now sits right after the username in the name column. `.captain-badge` shrunk from 20 → 16 px (`w-4 h-4`, `text-[9px]`) so it doesn't overpower the 12 px name. Both the partial and the JS renderer use a `[data-cap-slot]` marker the captain-assign code can find. `assignCaptains()` extracted as a shared helper used by both `moveChip()` and `snakeBalance()`.
- **Match-card player display: emoji → SVG.** [`_components/player_chip.html`](../templates/_components/player_chip.html) (used after "Save Teams" + "Show players" in the match card) now renders the role glyph as an inline `<svg>` from `Icons.jsx` (Bat / Ball / AllRounder paths), tinted `sky-700 / red-600 / purple-700` to match the design system role colors. The emoji-only `role_emoji` filter is still used elsewhere (`role_badge.html`, etc.) but the player chip is now icon-driven.

### Seed data
- 12 dummy users seeded from `initial_users.csv` (real Indian cricketers — virat, rohit, shubman, suryakumar, bumrah, shami, siraj, chahal, hardik, jadeja, ashwin, axar). All passwords `test1234`. `hardik` is the only staff member among the dummies. Session `id=2` has 11 yes-votes and 2 no-votes — provides realistic data for testing the snake-draft + skill-gap meter.

### Role-based ordering — applied everywhere players list
After every player movement (drag, swap, A/B, Auto-balance, page load) and on every server render, team rosters are sorted **batsmen → all-rounders → bowlers → other**, with combined-rating descending as the tie-breaker.

- View [apps/sessions/views.py](../apps/sessions/views.py) sorts `edit_team1_players` / `edit_team2_players` with a `_role_sort_key`.
- JS `sortTeamByRole(boxId)` reorders DOM children of each team container. Called from `moveChip()`, `snakeBalance()`, and the `DOMContentLoaded` init.
- New template filter `|sort_by_role` ([apps/accounts/templatetags/custom_filters.py](../apps/accounts/templatetags/custom_filters.py)) used in the match-card "saved teams" view.
- Side-effect: **captain becomes the highest-rated batsman** by default (because batsmen sort to the top and captain = first in list).

### Match-card UX: always-visible roster
The match-card "Show players" toggle is gone. **Player lists render unconditionally** as a 2-col grid (Team A · Team B) directly inside the match card, sorted by `|sort_by_role`. Only the "Score" button (staff-only) remains as a collapsible affordance. Each player chip now uses the SVG role icons in `_components/player_chip.html` (Bat / Ball / AllRounder paths from `Icons.jsx`, tinted sky / red / purple) instead of the previous emoji glyphs.

---

## Pending — Phase 3 (new features)

### E. Wallet transaction history
- Add a Wallet history section to the profile page (or a dedicated `/wallet/` URL).
- Show all `Wallet` rows ordered by `date desc` with running balance computed from summed `amount`.
- Reference: dashboard JSX uses the soft-tinted stat tile pattern — reuse [stat_tile.html](../templates/_components/stat_tile.html) for the wallet header.
- Listed as Planned Enhancement #2 in [CLAUDE.md](../CLAUDE.md).

### F. Team balance / snake-draft
- Net-new screen — HTMX-driven snake-draft auto-balancer in the session detail.
- Algorithm: sort players by combined batting+bowling+fielding rating descending, alternate-pick to Team A/B.
- Skill-gap meter shows the rating delta between teams.
- Reference: [design_handoff/ui_kits/indcric_web/TeamBalanceScreen.jsx](ui_kits/indcric_web/TeamBalanceScreen.jsx).
- Skill file: [.claude/skills/team-management/SKILL.md](../.claude/skills/team-management/SKILL.md).

### G. Match result with scorecards
- Existing skeleton at [cric/templates/cric/pages/match_detail.html](../cric/templates/cric/pages/match_detail.html) needs the full hero + MOTM + innings tabs + batting/bowling tables.
- Likely new models: `MatchInnings`, `PlayerMatchStats` (currently only `PlayerProfile` aggregates exist).
- Reference: [design_handoff/ui_kits/indcric_web/MatchResultScreen.jsx](ui_kits/indcric_web/MatchResultScreen.jsx).

### H. Notifications tabbed feed
- Net-new screen and likely a new `Notification` model.
- Reference: [design_handoff/ui_kits/indcric_web/NotificationsScreen.jsx](ui_kits/indcric_web/NotificationsScreen.jsx).

### I. Onboarding 3-step refresh
- Existing template at [cric/templates/cric/pages/profile_onboarding.html](../cric/templates/cric/pages/profile_onboarding.html) needs visual refresh.
- Reference: [design_handoff/ui_kits/indcric_web/OnboardingScreen.jsx](ui_kits/indcric_web/OnboardingScreen.jsx).

### J. Mobile bottom nav
- Last item — fixed bottom nav for `< md` viewports.
- Listed as Planned Enhancement #6 in [CLAUDE.md](../CLAUDE.md).

---

## Known issues surfaced (out of scope for current work)

- **[cric/templates/cric/pages/poll_detail.html](../cric/templates/cric/pages/poll_detail.html)** uses `|mul` filter but is missing `{% load custom_filters %}` at the top. Pre-existing bug; surfaces as `TemplateSyntaxError: Invalid filter: 'mul'` if anyone navigates to a poll detail page. **One-line fix:** add `{% load custom_filters %}` after `{% extends 'base.html' %}`.

---

## Conventions to keep using

- **No REST/JSON.** Server-rendered HTML only.
- **HTMX-first.** New interactive features use `hx-get` / `hx-post` + partials.
- **Staff-only mutations.** Wrap admin actions with `@staff_member_required`.
- **Decimal money.** Never use `float` for currency.
- **Atomic multi-model writes.** Wrap in `transaction.atomic()`.
- **Tailwind-only styling.** No new CSS files. The `colors_and_type.css` in this handoff is reference, not imported.
- **Compose with partials.** When a new screen needs an alert / badge / button / session-card / stat tile / eyebrow / rating bar — use `_components/`.
- **CSS-only additions.** Foundation pass deliberately did NOT modify any existing class. Continue this rule: new variants are new classes; never tweak `.btn-primary` etc.

---

## Next Steps

Recommended order:

1. **Commit uncommitted work** — signup refresh + dashboard auth-tier gating + session detail refresh + cost-split bug fix + profile refresh. Suggested message: `Phase 2 design refresh: signup, dashboard, session detail, profile`.
2. **Payments refresh** (Slice D) — closes out Phase 2; settlement-plan logic is the biggest unknown.

After Phase 2 is done, regroup before starting Phase 3 — those slices are net-new features (not refreshes) and may need data-model changes.

---

## Commit log (design overhaul)

- `a0f9412` — Adopt new design system: foundation + login + dashboard refresh
