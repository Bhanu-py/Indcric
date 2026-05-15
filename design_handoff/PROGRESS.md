# IndCric Design Overhaul — Progress & Handoff

Single source of truth for **where the design refresh stands and what to do next**.
Update this file at the end of every working session so any machine (or future Claude session) can pick up without re-discovery.

Last updated: **2026-05-15**
Last commit: **`a0f9412` — Adopt new design system: foundation + login + dashboard refresh**
Branch: **`master`** (1 commit ahead of `origin/master`, **not pushed**)

---

## How to resume on another machine

1. `git pull` to fetch commit `a0f9412` (push first from the source machine if not pushed yet).
2. Activate venv: `source .venv/Scripts/activate` (bash) or `.venv\Scripts\activate` (PowerShell).
3. Run `docker-compose up -d` (Postgres) and `python manage.py runserver`.
4. Open this file (`design_handoff/PROGRESS.md`) and pick the next pending slice below.
5. Tell Claude:
   > "Read `design_handoff/PROGRESS.md`. We're picking up at the next pending slice — start <slice name>."

---

## Phase plan at a glance

| Phase | Slice | Status |
|---|---|---|
| 1 | Foundation (tokens, partials, assets) | **Done** |
| 2 | Login screen refresh | **Done** |
| 2 | Dashboard refresh | **Done** |
| 2 | Sign-up screen refresh | **Pending** |
| 2 | Session detail refresh | **Pending** |
| 2 | Profile refresh | **Pending** |
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

## Pending — Phase 2 (visible screen refreshes)

### A. Sign-up — [templates/account/signup.html](../templates/account/signup.html)
**Goal:** Apply the same dark-hero + form-right pattern from login. The signup page currently uses a different layout.

**Reference:** No dedicated JSX for signup — reuse the structure of [design_handoff/ui_kits/indcric_web/LoginScreen.jsx](ui_kits/indcric_web/LoginScreen.jsx) and adapt the heading + form fields.

**Plan:**
1. Read [templates/account/signup.html](../templates/account/signup.html) to inventory existing fields (username, email, password1, password2, plus any custom fields).
2. Reuse the dark-hero panel HTML verbatim from [templates/account/login.html](../templates/account/login.html) (factor it into `templates/account/_entrance_hero.html` so login and signup both `{% include %}` it).
3. Build the right-panel form with the new look. Heading: "Create your account". Subtitle: "Join your club's session board".
4. Use `_components/alert.html` for non-field errors.
5. Bottom link: "Already a member? Sign in →" → `account_login`.

**Verify:** `GET /accounts/signup/` → 200, fields validate as before.

### B. Session detail — [cric/templates/cric/pages/session_detail.html](../cric/templates/cric/pages/session_detail.html)
**Goal:** Refresh the most complex screen — hero strip, cost split, availability poll, two team grids, going list.

**Reference:** [design_handoff/ui_kits/indcric_web/SessionDetailScreen.jsx](ui_kits/indcric_web/SessionDetailScreen.jsx) + [design_handoff/preview/component-session-card.html](preview/component-session-card.html).

**Plan:**
1. Hero strip — `bg-gradient-to-r from-pitch-800 to-pitch-600` with date pill, name, location, time on the left and cost-per-person block on the right.
2. Cost split — three stat tiles (Hall fee, Per person, Confirmed in) using `_components/stat_tile.html`.
3. Poll section — use existing vote-bar plus stacked Yes/No counts, hide if no poll.
4. Two team grids side-by-side — use `_components/player_chip.html` for each member, captain pip via `is_captain`.
5. Going list — flat list of confirmed players with role glyphs.
6. Staff-only "Save teams" / "Smart split" buttons stay (smart-split is Phase 3).

**Touch points:** likely also `apps/sessions/views.py:session_detail_view` for any new context the layout needs.

**Skill file:** see [.claude/skills/session-workflow/SKILL.md](../.claude/skills/session-workflow/SKILL.md) for the model + state-flow rules before editing.

### C. Profile — [cric/templates/cric/pages/profile.html](../cric/templates/cric/pages/profile.html)
**Goal:** Identity gradient strip + editable skill ratings + career stat grid.

**Reference:** [design_handoff/ui_kits/indcric_web/ProfileScreen.jsx](ui_kits/indcric_web/ProfileScreen.jsx).

**Plan:**
1. Identity strip — `bg-gradient-to-r from-pitch-800 to-pitch-600`, avatar disc with `ring-amber-400`, name, @username, role badge.
2. Skill-ratings card — three rows (Batting 🏏 / Bowling 🎯 / Fielding 🤸) each using `_components/rating_bar.html` (the new 5-segment one, NOT the existing `.rating-bar` continuous bar).
3. Editable ratings: keep the existing inline-edit (hyperscript) flow; only the visual changes.
4. Career stats — 5 stat tiles via `_components/stat_tile.html` (Matches, Runs, Wickets, Catches, Stumps).
5. "Edit profile" button → existing `profile-settings` URL.

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

1. **Push the current commit** so the other PC can pull it (`git push -u origin master`).
2. **Sign-up screen refresh** (Slice A) — small surface, reuses the login hero, finishes the entrance flow.
3. **Session detail refresh** (Slice B) — most-used screen after dashboard; gives the app its second big visible bump.
4. **Profile refresh** (Slice C) — uses the new `rating_bar.html` partial for the first time in production.
5. **Payments refresh** (Slice D) — closes out Phase 2; settlement-plan logic is the biggest unknown.

After Phase 2 is done, regroup before starting Phase 3 — those slices are net-new features (not refreshes) and may need data-model changes.

---

## Commit log (design overhaul)

- `a0f9412` — Adopt new design system: foundation + login + dashboard refresh
