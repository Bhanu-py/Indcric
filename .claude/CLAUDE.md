# Claude Instructions for IndCric

## Available Skills

Load these skills when working on specific feature areas:

| Skill file | Use when |
|---|---|
| `skills/payments-wallet.md` | Payment tracking, wallet balance, cost splitting, Splitwise-style expenses |
| `skills/team-management.md` | Team assignment, smart balancing, match scoring, player stats |
| `skills/expense-splitting.md` | Group expense tracking beyond cricket sessions |
| `skills/session-workflow.md` | Session creation, attendance confirmation, polls, cost calculation |
| `skills/django-htmx-patterns.md` | Any new view, template, or interactive feature |

## How to Work on This Project

1. **Read before editing**: Always read the relevant model, view, and template files before making changes.
2. **Check the skill file first**: The skill for the feature area has patterns, gotchas, and model details.
3. **HTMX-first**: New interactive features should use HTMX partials, not full page reloads.
4. **No REST API**: Do not add DRF or JSON endpoints — this project uses server-rendered HTML only.
5. **Money is always Decimal**: Never use float for currency. Use `from decimal import Decimal`.
6. **Staff-only mutations**: Wrap admin actions with `@staff_member_required`.
7. **Atomic transactions**: DB writes involving multiple models (e.g. wallet + payment) must be wrapped in `transaction.atomic()`.

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

1. **Group expense splitting** — Splitwise-like Expense + ExpenseSplit models and UI (see `skills/expense-splitting.md`)
2. **Wallet transaction history UI** — show all Wallet rows with running balance on profile page
3. **Smart team balancing** — auto-split button in session detail that uses ratings algorithm (see `skills/team-management.md`)
4. **Match scorecards** — add runs/wickets fields to Team; entry form in session detail
5. **Individual session stats** — PlayerMatchStats model linked to SessionPlayer
6. **Mobile bottom nav** — responsive navigation for mobile users
