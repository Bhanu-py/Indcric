# IndCric Web — UI Kit

A faithful, **interactive** recreation of the IndCric cricket-club management
web app, ported from the Django/HTMX/Tailwind codebase into self-contained
React (JSX + Babel-in-browser).

The components here are visual recreations — they do not call a backend. They
exist to be copied into mocks, prototypes, and slides without hand-rolling
the styling each time.

## Files

| File | What it is |
|---|---|
| `index.html`               | App shell, routing, sample data, demo data wiring |
| `Icons.jsx`                | Heroicons-outline set + the IndCric cricket-ball glyph |
| `Primitives.jsx`           | `Button`, `Card`, `Badge`, `Eyebrow`, `Input`, `RatingBar`, `VoteBar` |
| `Header.jsx`               | `pitch-900` sticky bar with manage / user dropdowns; `Avatar` lives here too |
| `SessionCard.jsx`          | Dashboard session tile (date pill, poll bar, hover state) |
| `LoginScreen.jsx`          | Split-pane sign-in with the cricket-ground watermark |
| `DashboardScreen.jsx`      | Welcome + upcoming/previous session grids |
| `SessionDetailScreen.jsx`  | Hero card, cost split, poll buttons, two team cards |
| `ProfileScreen.jsx`        | Avatar, role badge, skill bars, career-stat tiles |
| `PaymentsScreen.jsx`       | Match picker + paid/pending checklist |

## Flow you can click through

1. **Sign In** — any non-empty username works; account is mocked to staff.
2. **Dashboard** — three upcoming, three previous. Click a card to drill in.
3. **Session Detail** — vote yes/no, see two teams populated, scroll the
   "Going" chip row.
4. **Manage ▸ Payments** — pick a match, toggle paid/pending checkboxes.
5. **Manage ▸ Users** — member directory with role badges.
6. **Manage ▸ Create Session** — form layout only (no submit).
7. **Avatar ▸ My Profile** — toggle Edit Profile to flip the rating rows into
   number inputs.

## Component scope: what we copied vs. what we left out

**Recreated:**
- Header chrome (pitch-900 bar, amber ball mark, two dropdowns)
- Cards (rounded-2xl, shadow-sm, hover→shadow-md, top accent bars)
- Buttons (six variants, three sizes, scale-95 press)
- Badges (seven tones, including role-emoji variants)
- Form inputs (icon prefix, focus ring, error state)
- Rating bar / Vote bar
- Player chip + captain dot
- Stat tiles
- Cricket-ground SVG hero watermark

**Intentionally omitted** (not in the codebase / not worth replicating):
- The Django admin
- HTMX partials (everything here is plain client-side React)
- Real auth, real seeding, real DB persistence

## Why this exists

When designing screens for IndCric — new flows, member-facing pages,
WhatsApp-community surfaces — paste these components in instead of rebuilding
the chrome. The visual vocabulary (pitch green primary, amber accent, warm
stone neutrals, rounded-2xl cards, Inter throughout) is already correct.
