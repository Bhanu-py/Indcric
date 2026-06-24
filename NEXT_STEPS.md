# ⚡ Next Steps: How to Finalize Implementation

## 📦 Step 1: Generate Database Migration

```bash
cd c:\Users\ZV6699\OneDrive - ENGIE\Documents\GitHub\Indcric

# Create migration
python manage.py makemigrations matches

# This will create a file like: apps/matches/migrations/0XXX_add_temporaryscoringaccess.py
```

**Expected Output:**
```
Migrations for 'matches':
  apps/matches/migrations/0XXX_add_temporaryscoringaccess.py
    - Create model TemporaryScoringAccess
```

---

## ✅ Step 2: Review Migration (Optional but Recommended)

```bash
# View the SQL that will be executed
python manage.py sqlmigrate matches 0XXX

# Verify it looks correct before running
```

---

## 🗄️ Step 3: Apply Database Migration

```bash
# Apply the migration
python manage.py migrate

# Expected output:
# Operations to perform:
#   Apply all migrations: accounts, banking, ..., matches, ..., sessions, etc.
# Running migrations:
#   Applying matches.0XXX_add_temporaryscoringaccess... OK
```

---

## 🧪 Step 4: Run Tests to Verify Everything Works

```bash
# Run only the new tests
python manage.py test apps.matches.TemporaryScoringAccessTests -v 2

# Run all matches tests to ensure nothing broke
python manage.py test apps.matches -v 2

# Run all tests
python manage.py test
```

**Expected Results:**
- ✅ All 11 new tests pass
- ✅ All existing matches tests pass
- ✅ No errors or failures

---

## 🌐 Step 5: Test in Django Admin

### 5a. Create a Superuser (if you don't have one)
```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### 5b. Start Development Server
```bash
python manage.py runserver
```

### 5c. Log into Admin
- Navigate to: http://localhost:8000/admin/
- Log in with superuser credentials

### 5d. Test Grant Access
1. Go to "Matches" → "Temporary Scoring Access"
2. Click "Add Temporary Scoring Access"
3. Fill in:
   - **User**: Select a player
   - **Session**: Select a session
   - **Duration minutes**: Select "1 hour"
   - **Reason**: "Testing access"
4. Click "Save"
5. Verify:
   - ✅ granted_by is auto-filled with your user
   - ✅ expires_at is 1 hour from now
   - ✅ Access appears in the list

### 5e. Test Revoke Action
1. Select the access you just created
2. In "Action" dropdown, select "Revoke selected access"
3. Click "Go"
4. Verify the access is now marked as inactive

### 5f. Test Extend Action
1. Create another access
2. Select it
3. In "Action" dropdown, select "Extend access by 1 hour"
4. Click "Go"
5. Verify expires_at increased by 1 hour

---

## 🎮 Step 6: Manual Testing - End-to-End Flow

### Test Case 1: Player With Valid Access Can Score

```python
# In Django shell: python manage.py shell

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.sessions.models import Session
from apps.matches.models import Match, TemporaryScoringAccess
from datetime import time as dtime
from decimal import Decimal

User = get_user_model()

# Create users
admin_user = User.objects.create_user(username='admin', password='pass', is_staff=True)
player_user = User.objects.create_user(username='player', password='pass')

# Create session and match
session = Session.objects.create(
    name='Test Session',
    cost=Decimal('0'),
    duration=Decimal('3'),
    date=timezone.now().date(),
    time=dtime(18, 0),
    location='GUSB'
)

match = Match.objects.create(session=session, name='Test Match', overs_limit=20)

# Grant temporary access
access = TemporaryScoringAccess.objects.create(
    user=player_user,
    session=session,
    granted_by=admin_user,
    expires_at=timezone.now() + timedelta(hours=2),
    is_active=True,
    reason='Testing'
)

# Verify access is valid
print(f"Access is valid: {access.is_valid}")  # Should print: True
print(f"Expires at: {access.expires_at}")

# Verify can_score works
from apps.matches.views import _can_score
from unittest.mock import Mock

request = Mock()
request.user = player_user

can_score = _can_score(request, match)
print(f"Player can score: {can_score}")  # Should print: True
```

### Test Case 2: Player Without Access Cannot Score

```python
# Create another player
player2 = User.objects.create_user(username='player2', password='pass')

request2 = Mock()
request2.user = player2

can_score2 = _can_score(request2, match)
print(f"Player2 can score: {can_score2}")  # Should print: False
```

### Test Case 3: Expired Access Cannot Score

```python
# Create expired access
expired_access = TemporaryScoringAccess.objects.create(
    user=player2,
    session=session,
    granted_by=admin_user,
    expires_at=timezone.now() - timedelta(minutes=1),  # Already expired
    is_active=True
)

print(f"Expired access is_valid: {expired_access.is_valid}")  # Should print: False

can_score_expired = _can_score(request2, match)
print(f"Player2 can score (with expired access): {can_score_expired}")  # Should print: False
```

---

## 🧹 Step 7: Test Management Command

```bash
# Create some expired access first
python manage.py shell
```

```python
from apps.matches.models import TemporaryScoringAccess
from django.utils import timezone
from datetime import timedelta

# Create test data
expired = TemporaryScoringAccess.objects.create(
    user=player_user,
    session=session,
    granted_by=admin_user,
    expires_at=timezone.now() - timedelta(hours=1),
    is_active=True
)
print(f"Created expired access: {expired}")
```

```bash
# Exit shell (Ctrl+D on Linux/Mac, Ctrl+Z then Enter on Windows)

# Test dry run
python manage.py revoke_expired_scoring_access --dry-run

# Should show what would be revoked

# Actually revoke
python manage.py revoke_expired_scoring_access

# Verify it was revoked
python manage.py shell
```

```python
expired.refresh_from_db()
print(f"Access is_active: {expired.is_active}")  # Should print: False
```

---

## 📝 Step 8: Update URL Routing (If Using New Views)

If you want to use the grant/revoke/list views, add to `apps/matches/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... existing patterns ...
    
    # Temporary scoring access management
    path('session/<int:session_id>/grant-access/', views.grant_scoring_access_view, name='grant_scoring_access'),
    path('access/<int:access_id>/revoke/', views.revoke_scoring_access_view, name='revoke_scoring_access'),
    path('session/<int:session_id>/access-list/', views.scoring_access_list_view, name='scoring_access_list'),
]
```

---

## 📱 Step 9: Create Templates (Optional)

You can optionally create templates for the access management views:

### `cric/pages/grant_scoring_access.html`
```html
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1>Grant Scoring Access</h1>
    <p>Grant temporary scoring access for: <strong>{{ session.name }}</strong></p>
    
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn btn-primary">Grant Access</button>
        <a href="{% url 'session_detail' session.id %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}
```

### `cric/pages/confirm_revoke_access.html`
```html
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1>Revoke Scoring Access</h1>
    <div class="alert alert-warning">
        <p>Are you sure you want to revoke <strong>{{ access.user.username }}</strong>'s 
        scoring access for <strong>{{ access.session.name }}</strong>?</p>
    </div>
    
    <form method="post">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger">Yes, Revoke</button>
        <a href="{% url 'session_detail' access.session.id %}" class="btn btn-secondary">Cancel</a>
    </form>
</div>
{% endblock %}
```

### `cric/pages/scoring_access_list.html`
```html
{% extends 'base.html' %}

{% block content %}
<div class="container mt-5">
    <h1>Scoring Access - {{ session.name }}</h1>
    
    <table class="table">
        <thead>
            <tr>
                <th>Player</th>
                <th>Granted By</th>
                <th>Expires</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for access in access_list %}
            <tr>
                <td>{{ access.user.username }}</td>
                <td>{{ access.granted_by.username|default:"System" }}</td>
                <td>{{ access.expires_at|date:"Y-m-d H:i" }}</td>
                <td>
                    {% if access.is_valid %}
                        <span class="badge badge-success">Valid</span>
                    {% else %}
                        <span class="badge badge-danger">Expired/Inactive</span>
                    {% endif %}
                </td>
                <td>
                    {% if access.is_active %}
                        <a href="{% url 'revoke_scoring_access' access.id %}" class="btn btn-sm btn-danger">Revoke</a>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

---

## 📚 Step 10: Documentation

Create a user guide for staff:

### Admin User Guide

**Granting Temporary Scoring Access:**

1. Log into Django Admin
2. Navigate to "Matches" section
3. Click "Temporary Scoring Access"
4. Click "Add Temporary Scoring Access"
5. Fill in the form:
   - **Player**: Select the player getting access
   - **Session**: Select the session/day
   - **Duration**: Select how long (30m, 1h, 2h, etc.)
   - **Reason** (optional): Why are you granting access
6. Click "Save"

The system will:
- Automatically record who granted it (you)
- Automatically set the expiration time
- Allow the player to score immediately
- Revoke access automatically after the duration

**Revoking Access Early:**

1. Go to "Temporary Scoring Access"
2. Find the access to revoke
3. Click the checkbox
4. Select "Revoke selected access"
5. Click "Go"

Access is revoked immediately.

**Extending Expiring Access:**

1. Go to "Temporary Scoring Access"
2. Find the access to extend
3. Click the checkbox
4. Select "Extend access by 1 hour"
5. Click "Go"

This adds 1 hour to the expiration time.

---

## 🎯 Verification Checklist

Before considering complete:

- [ ] Migration created and applied
- [ ] All tests pass
- [ ] Admin interface works
- [ ] Can grant access
- [ ] Can revoke access
- [ ] Can extend access
- [ ] Player with access can score
- [ ] Player without access cannot score
- [ ] Expired access blocks scoring
- [ ] Management command works
- [ ] No console errors
- [ ] No database errors

---

## 🚀 Ready to Deploy!

Once all steps complete:

1. **Commit changes** to your staging branch
2. **Push to repository**
3. **Create pull request** for review
4. **Merge to main** branch
5. **Deploy to production** following your deployment process

---

## 📞 Troubleshooting

### Migration Error: "ModuleNotFoundError"
**Solution**: Make sure imports in migration are correct

### Admin Page Won't Load
**Solution**: Restart Django server after migration

### Test Fails: "TemporaryScoringAccess DoesNotExist"
**Solution**: Migration not applied. Run `python manage.py migrate`

### Player Still Blocked with Valid Access
**Solution**: Check if expires_at is in the future. Use `access.is_valid` to verify.

### Access Works for Different Session
**Solution**: Check unique constraint - should only allow one per (user, session) pair

---

**All code is ready! Follow these steps and you're done.** ✅
