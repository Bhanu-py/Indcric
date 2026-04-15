# Skill: Session & Attendance Workflow

Use this skill when working on session creation, attendance confirmation, cost calculation, or the session detail page.

## Session Lifecycle

```
1. CREATED       → Session created (date, time, cost, location)
2. POLL OPEN     → Poll created; players vote yes/no
3. POLL CLOSED   → Poll closed by staff; attendance roster finalised
4. TEAMS SET     → Players assigned to Team A / Team B
5. CONFIRMED     → attendance_confirmed=True; cost_per_person calculated;
                   Payments created for all attendees
6. PAYMENTS DUE  → Each attendee's Payment.status = 'pending'
7. PAID          → Payment.status = 'paid' (cash or wallet)
```

## Key View: session_detail_view

Located in `cric/views.py`. Renders:
- Session metadata
- Poll (if exists) with vote counts and current user's vote
- Team assignments (Team A / Team B columns)
- Payment status per player (if attendance confirmed)

Returns `session_detail.html` (full) or HTMX partial as needed.

## Attendance Confirmation

When staff confirms attendance (`attendance_confirmed = True`):

```python
from decimal import Decimal

def confirm_attendance(session):
    attendees = SessionPlayer.objects.filter(session=session, attended=True)
    count = attendees.count()
    if count == 0:
        return

    cost_per_person = session.cost / Decimal(count)
    session.cost_per_person = cost_per_person
    session.attendance_confirmed = True
    session.save()

    for sp in attendees:
        Payment.objects.get_or_create(
            user=sp.user,
            session=session,
            defaults={
                'amount': cost_per_person,
                'status': 'pending',
                'method': 'cash',
            }
        )
```

## Cost Per Person

`session.cost_per_person` is always derived from `session.cost / confirmed_attendee_count`. Never store it manually — recalculate when attendance changes.

## Poll Integration

Each session has at most one Poll (OneToOne). The poll gathers availability before teams are set.

```python
# Check if current user voted
user_vote = Vote.objects.filter(poll=session.poll, user=request.user).first()
# user_vote.choice == 'yes' | 'no'

# Vote counts
yes_count = Vote.objects.filter(poll=session.poll, choice='yes').count()
no_count = Vote.objects.filter(poll=session.poll, choice='no').count()
```

## Session Detail Template Structure

```
session_detail.html
├── Session info card (date, time, location, cost)
├── Poll section (if session.poll exists)
│   ├── Voting buttons (if poll.is_open)
│   └── Results bar (always visible)
├── Teams section
│   ├── Team A column (list of SessionPlayer cards)
│   └── Team B column (list of SessionPlayer cards)
│       └── Team assignment form (staff only)
└── Payments section (if attendance_confirmed)
    └── Per-player payment status + toggle button
```

## Adding Attendance Mark (match_attendance_detail_view)

In `cric/views.py`. Takes a match/session pk, shows players, lets staff tick attendance:

```python
# POST: list of attended user IDs
attended_ids = request.POST.getlist('attended_users')
SessionPlayer.objects.filter(session=session).update(attended=False)
SessionPlayer.objects.filter(session=session, user_id__in=attended_ids).update(attended=True)
```

## Creating a Session (create_session_view)

POST fields: `name`, `cost`, `duration`, `date`, `time`, `location`

```python
session = Session.objects.create(
    name=form.cleaned_data['name'],
    cost=form.cleaned_data['cost'],
    ...
    created_by=request.user,
)
return redirect('cric:session_detail', pk=session.pk)
```

## Common Context Variables for Session Detail

```python
context = {
    'session': session,
    'poll': getattr(session, 'poll', None),
    'user_vote': user_vote,           # Vote object or None
    'team_a': team_a_session_players, # QuerySet of SessionPlayer
    'team_b': team_b_session_players,
    'payments': payments_qs,          # QuerySet of Payment
    'cost_per_person': session.cost_per_person,
    'all_players': all_players_qs,    # For team assignment form
}
```

## Testing Checklist
- [ ] Session creation saves all fields correctly
- [ ] Poll can only be created once per session
- [ ] Voting after poll is closed returns an error
- [ ] Confirming attendance when 0 attendees is handled gracefully
- [ ] cost_per_person rounds to 2 decimal places (use Decimal, not float)
- [ ] Payment records are idempotent (get_or_create, not create)
- [ ] Session deletion cascades to Poll, Match, SessionPlayer, Payment
