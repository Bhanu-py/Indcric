# IndCric Design System

The visual + interaction language for **IndCric** — the in-house management
app for **Indian Cricket Ghent (ICG)**, a community cricket club in Ghent,
Belgium. The club hosts indoor / outdoor sessions, splits hall costs across
members, runs availability polls, balances teams by skill, and stays in
touch via a WhatsApp community.

This folder is the single source of truth for type, color, components, and
voice across anything that wears the IndCric brand — the web app itself,
upcoming companion surfaces (WhatsApp-shareable cards, member-facing
microsites, decks).

## Sources used to build this system

| What | Where | Notes |
|---|---|---|
| Web codebase | <https://github.com/Bhanu-py/Indcric> | Django 5.1 + HTMX + Tailwind + Alpine; the entire visual system was lifted from here, especially `templates/base.html` and `templates/account/login.html` |
| Companion Flutter scaffold | <https://github.com/Bhanu-py/ICG> | Flutter cloud-codespaces starter; not yet styled to brand — keep on the radar |

> **Reader:** the GitHub repos above are the source of truth. If you need
> more fidelity (e.g. a screen we did not recreate), browse them directly —
> `templates/cric/pages/` covers session/profile/payments, and
> `templates/account/` covers auth.

## Index

```
README.md                ← you are here
SKILL.md                 ← Claude-Code-compatible skill manifest
colors_and_type.css      ← all CSS variables — type, color, spacing, radii, shadow, motion
assets/
  bat.png                ← brand sport icon, lifted from static/icons
  ball.png               ← brand sport icon, lifted from static/icons
preview/                 ← Design-System-tab cards (700×~150, one concept each)
  _card.css                shared styles for every card
  logo.html
  voice.html
  icons.html
  colors-pitch.html
  colors-stone.html
  colors-semantic.html
  type-display.html
  type-body.html
  spacing.html
  radius.html
  shadow.html
  buttons.html
  inputs.html
  badges.html
  alerts.html
  component-header.html
  component-session-card.html
  component-rating.html
  component-player.html
ui_kits/
  indcric_web/           ← interactive React recreation of the web app
    README.md
    index.html
    Icons.jsx
    Primitives.jsx
    Header.jsx
    SessionCard.jsx
    LoginScreen.jsx
    DashboardScreen.jsx
    SessionDetailScreen.jsx
    ProfileScreen.jsx
    PaymentsScreen.jsx
```

## What IndCric is, in one line

> Manage sessions, split costs, balance teams by skill, and track every
> match — built for the way the club really runs.

The product is calm, sporty, and web-native. It feels like a card-based
dashboard — not a stadium app, not a fan portal. It is built for one club,
not for the public.

## Audience & surfaces

- **Logged-in members** are the only people who see most of the app.
- **Captains / staff** (the small admin tier) get the Manage menu.
- **Outside surfaces** (WhatsApp share cards, sign-up landings, occasional
  Instagram one-offs) reuse the same green/amber palette and Inter type.

---

## CONTENT FUNDAMENTALS

Voice is direct, plainspoken, and a little cricket-warm. We write like a
captain shouting across the pitch, not a SaaS landing page.

### Person
- We speak to the reader as **you** ("Your pitch. Your play.").
- We refer to ourselves as **IndCric** when needed, never "we".
- Players are usually addressed by **first name or username**, never "User".

### Casing
- **Sentence case** for page titles ("Welcome back", "Skill Ratings",
  "Cost split").
- **UPPERCASE eyebrows** above sections — `tracking-wide`, 11px, 700 weight,
  e.g. `UPCOMING SESSIONS`, `PREVIOUS SESSIONS`.
- **Title Case** for buttons (`New Session`, `Mark Paid`, `Sign In`).
- All-lower **usernames**, always (`@bhanu`).

### Tone examples — verbatim from the product

| Surface | Copy |
|---|---|
| Login hero | "Your pitch. Your play. All in one place." |
| Login subtitle | "Manage sessions, split costs, balance teams by skill, and track every match — built for the way your club really runs." |
| Dashboard welcome | "Welcome back, Bhanu 👋 — Here's what's happening with IndCric" |
| Empty state | "No upcoming sessions." |
| Confirmation | "Delete this session?" |
| Vote summary | "7 Yes · 2 No · Closed" |
| Footer | "© 2026 IndCric · Built for the club." |

### Punctuation & glyphs
- The em-dash (`—`) and middle-dot (`·`) are heavily used as separators
  between meta items: `Tue · 18:00 · 1 h` / `Captain — bhanu`.
- A trailing arrow (`→`) on inviting links: `Create an account →`.
- Numbers like rupees / euros: `€7.20`. Decimal money. Hall fee currency is
  euro (Ghent).

### Emoji
- **Used, but tightly scoped.** Three slots only:
  - 🏏 batsman   🎯 bowler   ⭐ allrounder   🤸 fielding-rating row
  - 👋 in the welcome line, and nowhere else.
- Do **not** sprinkle emoji into buttons, alerts, headings, or marketing copy.
  Emoji is for player-role context only.

### Vibe
Friendly captain, light banter, never corporate. We celebrate small wins
("Team A won") without exclamation marks. We never gamify aggressively — no
streaks, no levels, no XP.

**Audience-gated surfaces (staff vs member vs guest):**

| Surface / element | Guest (logged out) | Member | Staff / admin |
|---|---|---|---|
| Dashboard upcoming cards | ✓ (click → sign in) | ✓ | ✓ |
| Dashboard previous cards | ✓ **locked** (click → sign in) | ✓ | ✓ |
| Dashboard **stats strip** (Sessions · 30d, Outstanding, Active members) | ✗ | ✗ | ✓ |
| Dashboard shortcut "Settle payments" | ✗ | ✗ | ✓ |
| Dashboard shortcut "Balance teams" | ✗ | ✓ (opens next session) | ✓ (opens next session) |
| Header "Payments" nav | ✗ | ✗ | ✓ |
| Session detail · view teams + pool | ✗ | ✓ read-only | ✓ |
| Session detail · **draft controls** (move player, auto-balance, share line-ups) | ✗ | ✗ | ✓ |
| Payments **Who-owes-whom** settlement tab | ✗ | ✗ | ✓ |
| Profile, Session detail, Notifications | ✗ | ✓ | ✓ |
| New Session CTA | ✗ | ✗ | ✓ |

When a guest clicks a locked card, route to Sign-in. Locked previous-session cards show a small **🔒 Sign in to see line-ups** pill on a soft white-blur overlay.

**Team balance lives inside Session detail** — it is not a separate route. The session detail page contains: hero → cost split → availability poll → **team balance + draft + available pool** → end. Staff get edit controls; members see the same teams read-only.

---

## VISUAL FOUNDATIONS

### Color
- **Primary — Pitch green** (`pitch-50…950`). A cricket-pitch green ramp.
  `pitch-700` is the workhorse primary fill. `pitch-800` is its hover.
  `pitch-900` is the **app header background**. `pitch-950` is the
  **sign-in hero background**.
- **Neutral — Stone** (warm greys: `stone-50…900`). `stone-50` is the page
  background; `stone-100` is the universal card border; text moves through
  `stone-400 → 500 → 700 → 900` for meta → body → labels → headings.
- **Accent — Amber 500.** The captain badge, the logo dot, the secondary
  CTA on dark backgrounds. Sparing — usually one amber thing per screen.
- **Semantic** — Emerald (success / yes-vote), Red (danger / no-vote),
  Sky (info / batsman badge), Purple-800 (allrounder badge).

### Type
- **Inter, Google Fonts.** Weights 400/500/600/700/800.
- Sizes: 11 (eyebrow / badge) → 12 (meta) → 13 (chip) → 14 (body, button) →
  16 (h3) → 18 (h2) → 24 (h1) → 38–48 (hero, sign-in only).
- Letter-spacing: `-0.015em` on display sizes (>24px), `+0.05em` on uppercase
  eyebrows.
- Line-height: 1.12 on hero, 1.3 on h1/h2, 1.5 on body.

### Spacing
- Tailwind 4-px scale, 1 (4px) → 12 (48px). Card padding sits at
  5–6 (20–24 px). Gap between cards is 4 (16 px).

### Backgrounds
- The dominant background is **flat warm grey** (`stone-50`).
- The only places we go dark are the **app header** (`pitch-900`) and the
  **sign-in hero panel** (`pitch-950`).
- **One gradient is in use:** `linear-gradient(90deg, pitch-800, pitch-600)`
  on the profile-header strip and the session-detail hero strip. Nothing
  else gradients.
- **One illustration motif** repeats on the sign-in hero: a low-opacity
  white SVG cricket ground (boundary, 30-yard circle, stumps). Always
  pointer-events:none, opacity 3–18 %. No photos, no stock imagery.
- No repeating textures. No grain. No noise.

### Animation
- **Fast and subtle.** Default duration 150 ms with `ease-out`. Slower for
  bar fills (500 ms) so the user sees the bar grow.
- Buttons press with `transform: scale(.95)`.
- Cards lift from `shadow-sm → shadow-md` on hover.
- Alpine `x-transition` on dropdowns: ease-out 150 ms in / ease-in 100 ms
  out, with a 4-px `-translate-y` and `scale-95` start.
- The live-status dot in the sign-in eyebrow pill has a 2-s `pulse`.
- **No bounces. No springs. No parallax.**

### Hover states
- **Cards:** shadow goes `sm → md`. Optional: heading colour `stone-900 →
  pitch-700`.
- **Buttons:** background darkens to the next stop (700 → 800, 500 → 600).
- **Nav items:** background `rgba(255,255,255,0.08)`.
- **Destructive icons** (delete) fade `opacity-0 → opacity-100` on group
  hover and tint red on direct hover.

### Press states
- `active:scale-95` everywhere on buttons.
- No colour shift on press beyond what hover already did.

### Borders
- Universal card border: `1px solid stone-100`. So light it almost only shows
  on white-on-white card-edges, but it's always there.
- Form inputs: `1px solid stone-200`, jumps to `transparent + 2-px pitch-500
  box-shadow` on focus.
- **No double borders, no border-radius differing across sides.**

### Shadows
- **Outer only.** Four steps:
  - `sm` — `0 1px 2px 0 rgb(0 0 0 / .05)` — default for cards.
  - `md` — combined `4px / 2px` — card hover.
  - `lg` — `10px / 4px` — avatar rings, occasional emphasis.
  - `xl` — `20px / 8px` — dropdowns.
- **No inner shadows.** No coloured shadows except the app-tile logo
  variant (pitch-shadow at low opacity).

### Transparency & blur
- Used on the **app header overlays** (`rgba(255,255,255,0.06–0.1)` for hover
  fills on a dark bar) and inside the **sign-in eyebrow pill**
  (`rgba(255,255,255,0.08)` over `pitch-950`).
- **No backdrop-blur anywhere.** No frosted glass.

### Color vibe of imagery
- Warm, balanced, sun-on-pitch — never cool/blue.
- No b&w, no grain, no duotones. PNG sport icons (bat, ball) sit in
  `assets/` and read at small sizes.

### Corner radii
- Three sizes, used consistently:
  - **8 px** (`rounded-lg`) → small chips, nav items, dropdown items.
  - **12 px** (`rounded-xl`) → buttons, form inputs, stat tiles.
  - **16 px** (`rounded-2xl`) → **cards** and modal sheets.
- Pills, avatars, vote bars and rating bars: `rounded-full`.

### Cards
- White background, 16 px radius, 1 px stone-100 border, shadow-sm.
- Many cards open with a **4-px solid accent bar** at the top
  (`pitch-600` for active, `stone-200` for past, `amber-500` for staff
  actions).
- Headers and bodies are split by a 1-px stone-100 horizontal divider.

### Layout rules
- The header is **sticky-top** with z-index 40 and `shadow-header`.
- Page content sits inside `max-w-7xl` (1280 px) for dashboard / payments,
  and `max-w-3xl` (768 px) for profile / single-item flows.
- Page padding: 24 px horizontally on tablet+, 32 px vertically.
- Three-up grid on desktop, two-up on tablet, one-up on mobile.

### Buttons
- Six variants (`primary` / `secondary` / `amber` / `success` / `danger` /
  `ghost`), four sizes (`sm` / `md` / `lg` / `xl`).
- Pill-ish but not full radius — 14 px corners.
- Optional leading icon (16 px). The icon and label sit on a 6-px gap.

### Form inputs
- 12 px radius, stone-200 border, 14 px text.
- Icon prefix uses a stone-400 outline icon, 16 px, positioned absolutely.
- Focus: kill the border, swap in a 2-px pitch-500 box-shadow ring.

### Badges
- Pills (`rounded-full`), 11 px, 600 weight, 100/800 tone pairing.
- Role badges always **include the emoji glyph** ahead of the label.

### Fixed elements
- The app header is the only persistently fixed element.
- No floating action buttons. No bottom-tab navigation on desktop. (A
  bottom-nav for mobile is listed in the codebase's "Planned Enhancements"
  but not yet present.)

---

## ICONOGRAPHY

### Stroke icons
- **Heroicons-outline** SVGs, **inlined** as raw `<svg>` markup in templates
  (the codebase never imports an icon library).
- 24-px viewBox, **2 px stroke**, round line caps and joins.
- Stroke colour inherits from `currentColor` so icons take on
  `stone-400` / `pitch-600` / `red-500` from their parent.
- Common icons used: home, calendar, pin (map), clock, wallet, users, cog,
  plus, check, trash, chevron-down, mail, lock, user, arrow-right, pencil,
  logout. See `preview/icons.html` for the actual set.

### Brand sport assets
- `assets/bat.png` (cricket bat) and `assets/ball.png` (cricket ball) come
  straight from `static/icons/` in the codebase. PNG, ≈ 36 × 36 in use.
- The **logo glyph** is a custom inline SVG of a cricket ball with a fly-by
  arc — defined in `Icons.jsx` (`CricketBall`) and reused on the header
  and the sign-in hero. Always white-on-amber for the app tile, white-on-
  white-tinted-square for the dark hero.

### Emoji
- Reserved for **player roles and ratings only**:
  - 🏏 batsman / batting
  - 🎯 bowler / bowling
  - ⭐ allrounder
  - 🤸 fielding
- Plus 👋 in the welcome line. **Nothing else.**
- Emoji never substitute for icons in nav, buttons, or alerts.

### Unicode chars
- Used as separators (`·`, `—`, `→`) in meta lines. No other unicode glyphs.

### Substitutions / flags for the user
- **No substitutions were needed.** Inter is loaded from Google Fonts
  exactly as the codebase does it. Icons are inlined verbatim.
- We **did not** copy the project's `favicon.ico` (it was not in the
  importable tree). If you need it, grab it from
  `https://github.com/Bhanu-py/Indcric/blob/master/static/favicon.ico`.

---

## How to use this system

- Reading order: this README → `colors_and_type.css` (variables) →
  `ui_kits/indcric_web/` (working components).
- For a new screen, **import `colors_and_type.css`** and the JSX files you
  need. The CSS variables work as-is; the JSX components expect React 18.
- For a new slide / one-off marketing surface, copy the cards from
  `preview/` for visual reference and reuse the variables.
- For production work in the Django codebase, **don't** reach for this
  folder — go straight to `templates/base.html` in Indcric where the same
  tokens already exist as Tailwind utilities.
