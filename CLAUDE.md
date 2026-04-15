# IndCric — Cricket Club Management App

## Project Overview

Django 5.1 web app for managing a cricket club: sessions, teams, attendance, payments, wallet balances, and group expense splitting. UI is server-rendered Django templates enhanced with HTMX (no full-page reloads) and Tailwind CSS.

## Tech Stack

| Layer | Tool |
|---|---|
| Framework | Django 5.1 |
| Frontend | Tailwind CSS (CDN), HTMX 2.0, Alpine.js, Hyperscript |
| Database | PostgreSQL (prod) / SQLite (local dev) |
| Auth | django-allauth |
| Tables | django-tables2 + django-filter |
| Forms | django-crispy-forms (Bootstrap 4 backend) |
| Static | Whitenoise |
| Server | Gunicorn (prod) |
| Deployment | Azure Web Apps |

## Directory Structure

```
Indcric/
├── cric/                   # Main app
│   ├── models.py           # All data models
│   ├── views.py            # Session, team, payment, attendance views
│   ├── views_users.py      # User profile, manage-users views
│   ├── views_polls.py      # Poll and voting views
│   ├── forms.py            # ProfileForm, EmailForm, UsernameForm
│   ├── forms_polls.py      # PollForm
│   ├── filters.py          # UserFilter (django-filter)
│   ├── tables.py           # UserHTMxTable (django-tables2)
│   ├── urls.py             # All URL patterns
│   ├── admin.py            # Django admin registration
│   ├── templatetags/
│   │   └── custom_filters.py  # get_item, mul filters
│   ├── management/commands/
│   │   └── seed_users.py   # Bulk user seeding from CSV
│   └── templates/cric/
│       ├── pages/          # Full-page templates
│       └── partials/       # HTMX partial templates
├── cric_core/
│   └── settings.py         # Django settings (env-driven DB config)
├── templates/              # Project-level base templates + allauth overrides
├── static/                 # CSS, icons
├── manage.py
├── requirements.txt
├── docker-compose.yml      # PostgreSQL for local dev
└── Procfile                # Gunicorn for production
```

## Data Models (cric/models.py)

### User (custom AbstractUser)
- `role`: batsman / bowler / allrounder
- `batting_rating`, `bowling_rating`, `fielding_rating`: DecimalField 0–5
- `wallet` (via reverse relation from Wallet model)

### Session
- `name`, `cost`, `duration`, `date`, `time`, `location`
- `cost_per_person` (DecimalField), `attendance_confirmed` (bool)
- `created_by` → User

### Poll / Vote
- One Poll per Session (OneToOne)
- Vote: user + choice (yes/no) + poll

### Match → Team → Player
- Match linked to Session
- Team has `captain` → User and a `name`
- Player: user + team + paid + role

### SessionPlayer
- Links a User to a Session with team assignment
- `paid` (bool), `team` → Team

### Attendance
- Wraps SessionPlayer with `attended` bool and optional Payment FK

### Payment
- user + session + amount + status (pending/paid) + method (wallet/cash)
- Unique: (user, session)

### Wallet
- user + amount + status + date (transaction log entries)

### PlayerProfile
- One-to-one with User
- `matches_played`, `runs_scored`, `wickets_taken`, `catches_taken`, `stumps_taken`

## Development Setup

```bash
# Start PostgreSQL
docker-compose up -d

# Activate virtualenv
source .venv/Scripts/activate     # Windows bash
# or
.venv\Scripts\activate            # Windows cmd/PowerShell

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed users (optional)
python manage.py seed_users

# Start dev server
python manage.py runserver
```

## Environment Variables (.env)

```
DEBUG=True
db_hostname=localhost
db_databasename=indcric_db
db_username=indcric_user
db_password=indcric_password
```

## Key Feature Areas

### 1. Session & Attendance
- Create sessions (date, cost, location)
- Poll players for availability (yes/no)
- Confirm attendance → auto-calculates cost_per_person

### 2. Team Management
- Assign players to Team A / Team B within a session
- Smart splitting: balance teams by batting/bowling ratings
- Track which team each player played in

### 3. Payments & Wallet
- Track per-session payments (cash or wallet)
- Wallet = advance balance; debited automatically when session confirmed
- Payment status: pending → paid

### 4. Group Expense Splitting (Splitwise-style)
- Beyond cricket: track group gathering expenses
- Any member logs an expense; split equally or custom amounts
- Wallet balances settle debts across the group

### 5. Scoring
- Match-level team scores (runs, wickets)
- Individual stats via PlayerProfile

### 6. Player Skills
- batting_rating / bowling_rating / fielding_rating (0–5)
- Editable by admin (manage-users) and by the player themselves (profile edit)

## Coding Conventions

- **HTMX-first**: prefer HTMX partial responses over full page reloads; check `request.htmx` in views
- **Staff-only mutations**: destructive or financial operations require `@staff_member_required`
- **Forms over raw POST**: always use Django Form classes for validation
- **Template tags**: use `get_item` for dict lookup in templates; `mul` for multiplication
- **No REST API**: all responses are HTML (Django templates), not JSON
- **URL namespaces**: app-level namespace is `cric`; manage routes live under `/manage/`
- **Partial templates**: HTMX targets use partials in `templates/cric/partials/`
- **Decimal money**: always use `DecimalField` with `max_digits=10, decimal_places=2` for monetary values

## URL Patterns (Key)

| Pattern | View | Notes |
|---|---|---|
| `/` | `home` | Upcoming + past sessions |
| `/session/<id>/` | `session_detail_view` | Teams, poll, payments |
| `/session/<id>/save-teams/` | `save_teams_view` | Staff only |
| `/manage/attendance/<id>/` | `match_attendance_detail_view` | Mark attendance |
| `/manage/payments/` | `payments_view` | Payment tracking |
| `/manage-users/` | `manage_users` | HTMX user table |
| `/profile/` | `profile_view` | Own profile + stats |
| `/profile/<username>/` | `profile_view` | Any user's profile |

## Planned Enhancements

- [ ] Expense splitting for non-cricket group gatherings (Splitwise-style)
- [ ] Wallet top-up and transaction history UI
- [ ] Smart team balancing by skill rating
- [ ] Match scorecards (runs, wickets per team)
- [ ] Individual batting/bowling stats per session
- [ ] Mobile-optimised bottom navigation
