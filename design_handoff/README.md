# IndCric Design System — Claude Code Handoff

Drop this bundle into the **Indcric repo** alongside the Django app. Then start a Claude Code session in VS Code and point it at this folder — everything Claude needs to bring the design system live in production is here.

> **What this is.** The HTML and JSX inside `preview/` and `ui_kits/indcric_web/` are **design references**. They show exactly how every component should look, feel, and behave, but they are written as a Babel-runtime React prototype to be browseable offline. They are **not** meant to be copy-pasted into the production app.
>
> **What you should do with it.** Recreate the designs inside the existing Indcric codebase — Django templates + HTMX + Tailwind + Alpine.js — using the patterns that already live in `templates/base.html`. The design tokens in `colors_and_type.css` already match the Tailwind config in the repo, so most work is template-level changes.

---

## Fidelity

**High-fidelity.** Every component in `preview/` is a final, pixel-precise specification:

- Final colour palette (pitch-green ramp + warm stone neutrals + amber accent + semantic ramps)
- Final type scale (Inter, weights 400-700, sizes 11→48 px)
- Final radii (8 / 10 / 16 px), borders (1 px stone-100), shadows (sm/md/lg/xl)
- Final motion (150 ms ease-out default, no springs)
- Final voice (sentence case titles, mono micro-labels, sparingly applied emoji)

When you implement a screen, you can treat the spacing, fonts and colours in the prototype as ground truth.

---

## Bundle contents

```
design_handoff/
├─ README.md                  ← you are here · how to use this bundle
├─ DESIGN_SYSTEM.md           ← full design-system writeup (voice, motion, layout rules, etc)
├─ colors_and_type.css        ← CSS variables · single source of truth for tokens
├─ assets/
│  ├─ logo-mark.png           ← brand mark · comet-ball monogram (square)
│  ├─ bat.png                 ← sport icon · for marketing / empty states
│  └─ ball.png                ← sport icon · for marketing / empty states
├─ preview/                   ← every component on a 700-wide card · use for spec lookup
└─ ui_kits/indcric_web/       ← working React prototype · use to see flows + interactions
```

### How to read the preview cards
Each `preview/*.html` is one component, on a 700-wide white card on stone-50. Open it in a browser to see the exact pixel values, then translate to Tailwind utilities in your templates. The cards group by:

| Card | What it specifies |
|---|---|
| `colors-pitch.html` / `colors-stone.html` / `colors-semantic.html` | Full palette ramps |
| `type-display.html` / `type-body.html` | Display + body type scale |
| `spacing.html` / `radius.html` / `shadow.html` | Spacing scale, radii, shadow stops |
| `buttons.html` | All six button variants, three sizes — slim (13 px / 500 weight / 8 px radius) |
| `inputs.html` | Form inputs (10 px radius, 13 px text, pitch-500 focus ring) |
| `badges.html` | Status badges + role badges (Set C glyphs); icon-only pill is the default |
| `alerts.html` | Info / success / warn / error |
| `component-rating.html` | 5-segment skill bar, rounds to halves, stone-800 fills |
| `component-player.html` | Player chip + stat block (typographic columns) + stat tile (soft tint) |
| `component-session-card.html` | Session card — date pill, location, poll bar, captain pip |
| `component-header.html` | App header — pitch-900, roundel logo, nav, bell, user menu |
| `icons.html` | 24-px icon set, 1.75 stroke, role-tinted |
| `logo.html` | Comet ball mark, B stacked wordmark, C horizontal lockup |
| `voice.html` | Copywriting do's and don'ts |

### How to read the React prototype
`ui_kits/indcric_web/index.html` is a fully clickable hi-fi of every screen, with a Tweaks panel and a floating screen-switcher. Use it to:

- Watch hover states, focus rings, and transitions in action
- Walk a flow end-to-end (login → dashboard → session detail → team balance → match result)
- Confirm copy and microcopy

Don't port the inline-styled React into Django — port the **design** into the existing Tailwind template system.

---

## Screens included

| Screen | File | What it does |
|---|---|---|
| **Login** | `LoginScreen.jsx` | Dark cricket-hero left + form right |
| **Dashboard** | `DashboardScreen.jsx` | Welcome row + snapshot strip + upcoming/past sessions |
| **Session detail** | `SessionDetailScreen.jsx` | Hero + cost split + availability poll + two teams + going list |
| **Profile** | `ProfileScreen.jsx` | Identity card + skill ratings (editable) + career stats |
| **Payments** | `PaymentsScreen.jsx` | "By match" tab + "Who owes whom" settlement plan |
| **Team balance / draft** | `TeamBalanceScreen.jsx` | Snake-draft auto-balancer + skill-gap meter |
| **Notifications** | `NotificationsScreen.jsx` | Tabbed activity feed |
| **Onboarding** | `OnboardingScreen.jsx` | 3-step first-time member flow |
| **Match result** | `MatchResultScreen.jsx` | Result hero + MOTM + innings tabs + batting / bowling / FOW / highlights |

---

## Design tokens at a glance

All tokens live in `colors_and_type.css`. The Indcric repo already exposes the same names through Tailwind utilities (`bg-pitch-700`, `text-stone-500`, `rounded-2xl` etc.). When in doubt, prefer Tailwind utility classes over inline CSS.

| Token group | Values (most-used) |
|---|---|
| **Pitch** (primary green) | `pitch-50/100/400/500/600/700/800/900/950` |
| **Stone** (neutral) | `stone-50/100/200/300/400/500/600/700/800/900` |
| **Semantic** | `emerald-100/500/600/800` · `red-50/100/500/600/700/800` · `amber-50/100/400/500/600/800` · `sky-100/500/800` · `purple-100/800` |
| **Type** | Inter 400/500/600/700; sizes 11/12/13/14/16/18/22/24/40 px |
| **Radii** | 8 px (chips), 10 px (inputs, tiles), 16 px (cards) |
| **Shadows** | `--shadow-sm/md/lg/xl` |
| **Motion** | 150 ms `ease-out` default, 500 ms for bar fills |

### Component primitives — what each looks like

| Primitive | Spec |
|---|---|
| **Button** | 8 px radius, 13 px / 500 weight, 7×14 padding. Primary fill pitch-700 → pitch-800 hover. Secondary white + stone-300 border. `active:scale-95`. |
| **Card** | white, 16 px radius, 1 px stone-100 border, shadow-sm → shadow-md on hover. Optional 4 px accent bar at top. |
| **Badge** | pill, 11 px / 600 weight, 100-shade bg + 800-shade fg. |
| **Role badge** | Outline glyph (bat / ball / allrounder / keeper) inside the badge or as a 22 px icon-only pill. |
| **Skill rating** | 5 capped segments, stone-800 filled / stone-100 empty, rounded to halves with a hard 50 % gradient. |
| **Player chip** | 8 px radius, hairline border tinted by role (sky / red / purple / stone). Avatar disc inside, role glyph trailing, optional captain pip. |
| **Stat column** | Mono 9 px UPPERCASE label with leading colour-dot, 24 px `tnum` numeric. Separated by 1 px stone-100 rule. |
| **Stat tile** | 10 px radius soft tint (sky / red / emerald / amber / pitch), same mono label + tnum numeric, optional delta in mono. |
| **Input** | 10 px radius, 13 px text, stone-200 border, 2 px pitch-500 focus shadow. |
| **Alert** | 10 px radius, 50-shade bg / 100-shade border / 800-shade fg, glyph + title + body + optional action. |

---

## Voice & copy

- **Person.** Reader is **"you"**. Players addressed by **first name or @username**.
- **Casing.** Sentence-case titles. Mono UPPERCASE eyebrows. Title Case buttons. all-lower usernames.
- **Separators.** `·` (middle-dot) for meta-line groupings. `—` (em-dash) for asides. `→` for inviting links.
- **Emoji.** Only in: 🏏 batsman, 🎯 bowler, ⭐ allrounder, 🤸 fielding, 👋 welcome. **Nowhere else.** (Iconography otherwise uses outline SVGs.)
- See `preview/voice.html` and the `DESIGN_SYSTEM.md` "CONTENT FUNDAMENTALS" section for verbatim tone examples.

---

## Iconography

- **Stroke icons** — Heroicons-outline style, **inlined as raw `<svg>`** in templates. 24-px viewBox, **1.75 stroke**, round caps + joins. Stroke colour from `currentColor`. Default tone is the semantic role (sky for batting / people, red for ball / destructive, pitch for schedule / positive, amber for venue / alerts, emerald for money / success, purple for allrounder, stone for neutral). The full inventory is in `preview/icons.html` and the JSX source is `ui_kits/indcric_web/Icons.jsx` — copy paths from there.
- **Brand mark** — `assets/logo-mark.png` is the canonical comet-ball monogram. It has a white background, so on dark surfaces (the app header / sign-in hero) wrap it in a soft white tile with `~22 %` radius so the cricket-ball + flame stay legible.
- **Sport assets** — `assets/bat.png` and `assets/ball.png` — for empty states, splash screens and marketing surfaces. Never inside dense UI rows.

---

## How to use this with Claude Code

1. Copy the `design_handoff/` folder into your Indcric repo root.
2. Open the repo in VS Code, start a Claude Code session.
3. Tell Claude: *"Read `design_handoff/README.md` and `design_handoff/DESIGN_SYSTEM.md`, then open one of the previews to understand the visual system. We'll be implementing screen X next — port the design into our existing Django + HTMX + Tailwind templates."*
4. Point Claude at the matching `preview/*.html` and `ui_kits/indcric_web/*Screen.jsx` files for each screen you want to ship.
5. Ship template-by-template — start with the slim Button + Badge + Card refresh in `templates/_components/`, then move to full screens.

### Translation guide — prototype → Django

| Prototype | Django target |
|---|---|
| Inline-styled JSX (`<div style={{padding: 18, ...}}>`) | Tailwind utility classes on Django template tags |
| `Card`, `Button`, `Badge` JSX components | Includable partials in `templates/_components/` |
| `useState` for vote, settlement, draft moves | HTMX `hx-post` + Alpine.js `x-data` |
| `Tweaks` panel | Drop — production has no tweak panel |
| Routes via React state | Django URL conf + view templates |
| Sample data in `index.html` | Real ORM querysets in views |

---

## Files index

| Use this for ... | Open this file |
|---|---|
| The full design-system doctrine (voice, motion, etc) | `DESIGN_SYSTEM.md` |
| Tokens as CSS variables | `colors_and_type.css` |
| One-component visual reference | `preview/<component>.html` |
| Full clickable hi-fi prototype | `ui_kits/indcric_web/index.html` (open in a browser) |
| React source for a screen | `ui_kits/indcric_web/<Screen>.jsx` |

That's everything. Happy shipping.
