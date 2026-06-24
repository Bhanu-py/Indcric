# Quick Reference: Temporary Scoring Access

## 📂 Files Modified

| File | Changes |
|------|---------|
| `apps/matches/models.py` | ✓ Added `TemporaryScoringAccess` model |
| `apps/matches/admin.py` | ✓ Added `TemporaryScoringAccessAdmin` |
| `apps/matches/views.py` | ✓ Updated 11 views + added 3 new views |
| `apps/matches/forms.py` | ✓ Created `TemporaryScoringAccessForm` |
| `apps/matches/tests.py` | ✓ Added 11 test methods |
| `apps/matches/management/commands/revoke_expired_scoring_access.py` | ✓ New management command |

## 🎯 Model Structure

```python
TemporaryScoringAccess:
  - id: BigAutoField (PK)
  - user: ForeignKey → User
  - session: ForeignKey → Session
  - granted_by: ForeignKey → User (nullable)
  - granted_at: DateTimeField (auto_now_add)
  - expires_at: DateTimeField (required)
  - is_active: BooleanField (default=True)
  - reason: TextField (blank, default='')
  - Unique: (user, session)
```

## 🔐 Permission Check

```python
# Old (Staff Only)
if request.user.is_staff:
    # Can score

# New (Staff + Temporary Access)
if _can_score(request, match):
    # Can score
```

## ⏰ Duration Options

- 30 minutes
- 1 hour
- 2 hours
- 3 hours
- 5 hours
- Custom (1-1440 minutes)

## 🛠️ Admin Features

**List View:**
- User, Session, Granted By, Expiry Time, Status
- Filter: Active/Inactive, Session Date
- Search: Username, Session Name

**Actions:**
- ✓ Revoke Access (bulk)
- ✓ Extend Access by 1 Hour (bulk)

**Auto-Fill:**
- `granted_by` automatically set to current user
- Cannot edit user/session on update

## 📊 Database Queries

```python
# Check if user can score
access = TemporaryScoringAccess.objects.filter(
    user=user,
    session_id=match.session_id,
    is_active=True,
    expires_at__gt=timezone.now()
).exists()

# Get all active access for a session
active_access = TemporaryScoringAccess.objects.filter(
    session=session,
    is_active=True,
    expires_at__gt=timezone.now()
).select_related('user', 'granted_by')

# Find expired access
expired = TemporaryScoringAccess.objects.filter(
    is_active=True,
    expires_at__lte=timezone.now()
)
```

## 🧪 Test Coverage

| Test | Purpose |
|------|---------|
| `test_staff_can_score` | Verify staff always allowed |
| `test_regular_player_cannot_score_without_access` | Verify rejection without access |
| `test_player_with_valid_access_can_score` | Verify valid access allows scoring |
| `test_player_with_expired_access_cannot_score` | Verify expiry blocks access |
| `test_player_with_inactive_access_cannot_score` | Verify revocation blocks access |
| `test_access_unique_constraint` | Verify DB constraint |
| `test_access_is_valid_property` | Verify validity checks |
| `test_player_cannot_score_on_different_session` | Verify session isolation |
| `test_score_ball_requires_valid_access` | Verify endpoint checks |
| `test_access_grants_scoring_permissions_to_all_match_operations` | Verify all endpoints |
| `test_access_str_representation` | Verify readable string |

## 🚀 Deployment Steps

```bash
# 1. Pull latest code
git pull origin stage

# 2. Create migrations
python manage.py makemigrations matches

# 3. Check migration
python manage.py sqlmigrate matches <migration_number>

# 4. Apply migration
python manage.py migrate

# 5. Run tests
python manage.py test apps.matches.TemporaryScoringAccessTests

# 6. Start server
python manage.py runserver
```

## 🔄 Usage Flow

### Grant Access (Admin)
1. Go to Django Admin → Temporary Scoring Access
2. Click "Add Temporary Scoring Access"
3. Select:
   - Player (user)
   - Session
   - Duration
   - Optional reason
4. Click Save (granted_by auto-filled with current admin)

### Player Uses Access
1. Player navigates to scoring page
2. System checks:
   - Is staff? → YES → Allow
   - Has valid access for this session? → YES → Allow
   - Otherwise → Redirect with error
3. Player can score matches for that session

### Cleanup Expired Access
```bash
# View what would be revoked
python manage.py revoke_expired_scoring_access --dry-run

# Actually revoke
python manage.py revoke_expired_scoring_access
```

### Revoke Manually
1. Go to Django Admin
2. Find the access entry
3. Click Edit
4. Uncheck "is_active"
5. Click Save

## 📝 Field Descriptions

| Field | Type | Purpose |
|-------|------|---------|
| `user` | FK | Player receiving access |
| `session` | FK | Session they can score for |
| `granted_by` | FK | Admin who granted access |
| `granted_at` | DT | When access was created (auto) |
| `expires_at` | DT | When access expires |
| `is_active` | Bool | Can be manually revoked |
| `reason` | Text | Audit trail notes |

## ✅ Validation Rules

1. ✓ User must exist
2. ✓ Session must exist
3. ✓ expires_at must be in future (on creation)
4. ✓ Only one active access per (user, session)
5. ✓ Duration must be 1-1440 minutes

## 🔍 Audit Trail

All access grants are tracked:
- **WHO**: `granted_by` field
- **WHEN**: `granted_at` timestamp
- **FOR WHOM**: `user` field
- **FOR WHAT**: `session` field + `reason`
- **HOW LONG**: `expires_at` shows duration
- **STATUS**: `is_active` shows if revoked

## ⚠️ Important Notes

1. **No Cascade Delete**: Deleting user/session doesn't delete access (SET_NULL for granted_by)
2. **Lazy Expiry**: Checks happen at access time, not scheduled
3. **Session Specific**: Access works for ALL matches in that session, not individual matches
4. **Staff Unaffected**: Existing staff access works unchanged
5. **Backward Compatible**: No breaking changes to existing code

## 🎓 Code Examples

### Check Access Programmatically
```python
from apps.matches.models import TemporaryScoringAccess
from django.utils import timezone

# Check if player can score
has_access = TemporaryScoringAccess.objects.filter(
    user=player,
    session=session,
    is_active=True,
    expires_at__gt=timezone.now()
).exists()

# Or use the view helper
from apps.matches.views import _can_score
can_score = _can_score(request, match)
```

### Grant Access Programmatically
```python
from apps.matches.models import TemporaryScoringAccess
from django.utils import timezone
from datetime import timedelta

access = TemporaryScoringAccess.objects.create(
    user=player_user,
    session=session,
    granted_by=admin_user,
    expires_at=timezone.now() + timedelta(hours=2),
    reason="Primary scorer sick"
)
```

### List Valid Access
```python
from apps.matches.models import TemporaryScoringAccess

valid_access = TemporaryScoringAccess.objects.filter(
    session=session,
    is_active=True,
    expires_at__gt=timezone.now()
).select_related('user', 'granted_by')

for access in valid_access:
    print(f"{access.user.username}: {access.reason} (expires {access.expires_at})")
```

---

**Status**: ✅ Complete & Ready for Migration
**Syntax Check**: ✅ All files pass
**Test Suite**: ✅ 11 comprehensive tests
**Backward Compatible**: ✅ Yes
**Breaking Changes**: ❌ None
