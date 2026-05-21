# Claude Instructions for IndCric

## Available Skills

Skills auto-load by description match — you don't need to invoke them manually. They live in `.claude/skills/<name>/SKILL.md`:

| Skill | Triggers on |
|---|---|
| [payments-wallet](skills/payments-wallet/SKILL.md) | Payment tracking, wallet balance, cost splitting |
| [team-management](skills/team-management/SKILL.md) | Team assignment, smart balancing, match scoring, player stats |
| [expense-splitting](skills/expense-splitting/SKILL.md) | Group expense tracking beyond cricket sessions |
| [session-workflow](skills/session-workflow/SKILL.md) | Session creation, attendance confirmation, polls, cost calculation |
| [django-htmx-patterns](skills/django-htmx-patterns/SKILL.md) | Any new view, template, or interactive feature |

## Available Subagents

Delegate via the `Agent` tool with `subagent_type`:

| Subagent | Use for |
|---|---|
| `django-model-reviewer` | Review model/migration changes for Decimal money, atomic transactions, staff-only guards, cascade safety |
| `htmx-partial-writer` | Build new HTMX-driven views + partial templates following project conventions |

## How to Work on This Project

1. **Read before editing**: Always read the relevant model, view, and template files before making changes.
2. **Check the skill file first**: The skill for the feature area has patterns, gotchas, and model details.
3. **HTMX-first**: New interactive features should use HTMX partials, not full page reloads.
4. **No REST API**: Do not add DRF or JSON endpoints — this project uses server-rendered HTML only.
5. **Money is always Decimal**: Never use float for currency. Use `from decimal import Decimal`.
6. **Staff-only mutations**: Wrap admin actions with `@staff_member_required`.
7. **Atomic transactions**: DB writes involving multiple models (e.g. wallet + payment) must be wrapped in `transaction.atomic()`.
8. **Mobile-first**: Most users access IndCric on phones. See **Mobile-First Rules** below.

## Mobile-First Rules

Every new view, template, or partial must be designed for a phone screen first, then scaled up with Tailwind's `sm:` / `md:` / `lg:` prefixes. Touch is the default input.

### Tailwind defaults (already enforced in [base.html](../templates/base.html))

These component classes already include mobile-aware sizing — **use them, don't reinvent**:

| Class | Mobile | sm+ | Notes |
|---|---|---|---|
| `.btn-md` | ~44px tall | ~30px tall | Primary mobile CTA — use for Save/Submit/Confirm |
| `.btn-lg` / `.btn-xl` | ~46px / ~48px | compact | For hero CTAs |
| `.btn-sm` | ~22px tall | unchanged | **Inline secondary only** — never as a mobile primary action |
| `.form-input`, `.form-select` | 48px tall, 16px text | 40px, 13px | 16px text prevents iOS auto-zoom on focus |
| `.page-content`, `.page-content-narrow` | py-4, safe-area aware | py-8 | Already accounts for iPhone notch / home indicator |
| `.safe-bottom`, `.safe-top` | inset utilities | — | For fixed bars |

### Hard rules for new templates

- **Tap targets ≥ 44 × 44px.** Wrap small icons/checkboxes in a larger `<label>` or padded `<button>`.
- **Grid layouts start single-column.** Default `grid-cols-1`, opt into `sm:grid-cols-2` / `md:grid-cols-3`. Never use `grid-cols-3` without a responsive prefix unless the cells are <80px wide.
- **Native input types**: `type="tel"` for phone, `inputmode="numeric"` for runs/wickets/ratings, `type="date"` for dates, `type="email"` for email.
- **Never rely on hover**: every action must work on tap. No hover-only tooltips, no `hover:` shown-state.
- **No HTML5 drag-and-drop without a touch alternative.** `dragstart`/`drop` don't fire on touch — always provide tap-to-action buttons alongside.
- **Primary CTAs go in a sticky bottom bar on long forms.** Use `fixed bottom-0 inset-x-0 safe-bottom bg-white border-t border-stone-100 px-4 py-3 md:static md:border-0 md:p-0` so it floats on mobile, inlines on desktop.
- **Micro labels ≥ 12px.** Avoid `text-[10px]` / `text-[11px]` on mobile; use `text-xs sm:text-[10px]` if you need it dense on desktop.
- **Never assume a top dropdown is the way to navigate.** Surface primary destinations as inline links or a bottom nav.

### Pre-flight checklist for any new mobile-touching change

- [ ] Renders correctly at 360px wide (Chrome DevTools → "iPhone SE")
- [ ] All buttons & form inputs use the component classes above
- [ ] No tap target smaller than 44×44px
- [ ] Primary action visible without scrolling, or sticky-bottom on long forms
- [ ] Tested with iOS Safari simulator if possible (different scroll/input behavior than Chrome)

## Key Files to Know

| File | Purpose |
|---|---|
| `cric/models.py` | All data models |
| `cric/views.py` | Session, team, payment, attendance views |
| `cric/views_users.py` | User profile and management views |
| `cric/views_polls.py` | Poll and voting logic |
| `cric/forms.py` | ProfileForm, EmailForm, UsernameForm |
| `cric/urls.py` | All URL patterns |
| `templates/base.html` | Master template (HTMX, Tailwind, Alpine loaded here) |
| `cric/templates/cric/pages/session_detail.html` | Most complex template |
| `cric_core/settings.py` | Django settings (DB, auth, middleware) |

## Environment

- Local dev: SQLite or Docker PostgreSQL (`docker-compose up -d`)
- Prod: Azure Web Apps + PostgreSQL
- Python venv: `.venv/` in project root

## Run Commands

```bash
# Start local DB
docker-compose up -d

# Activate venv (Windows bash)
source .venv/Scripts/activate

# Migrate after model changes
python manage.py makemigrations && python manage.py migrate

# Start dev server
python manage.py runserver
```

## What's Planned (Priority Order)

1. **Group expense splitting** — Splitwise-like Expense + ExpenseSplit models and UI (see [expense-splitting](skills/expense-splitting/SKILL.md))
2. **Wallet transaction history UI** — show all Wallet rows with running balance on profile page
3. **Smart team balancing** — auto-split button in session detail that uses ratings algorithm (see [team-management](skills/team-management/SKILL.md))
4. **Match scorecards** — add runs/wickets fields to Team; entry form in session detail
5. **Individual session stats** — PlayerMatchStats model linked to SessionPlayer
6. **Mobile bottom nav** — responsive navigation for mobile users
