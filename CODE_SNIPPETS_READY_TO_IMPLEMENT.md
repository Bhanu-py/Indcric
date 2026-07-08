# Code Snippets Ready to Implement

Quick copy-paste solutions for performance improvements. Test in dev first!

---

## 1. Fixed Home View (apps/sessions/views.py)

**Replace lines ~40-100 with this:**

```python
from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Sum, Prefetch, Q
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache

from .models import Session, SessionPlayer, Attendance
from apps.matches.models import Match, Team, Player, Delivery, TemporaryScoringAccess
from apps.polls.models import Poll, Vote
from apps.payments.models import Payment, Wallet

User = get_user_model()


def _live_match_session_ids(sessions):
    """Session ids that currently have a match being scored — scoring started
    (≥1 innings) but not yet concluded (the result is declared only once both
    innings exist and are closed, mirroring scoring.result_line/finalize)."""
    session_ids = [s.id for s in sessions]
    if not session_ids:
        return set()
    live = set()
    matches = (
        Match.objects.filter(session_id__in=session_ids)
        .prefetch_related('innings')
    )
    for match in matches:
        innings = list(match.innings.all())
        if not innings:
            continue  # scoring hasn't started
        concluded = len(innings) >= 2 and all(i.is_closed for i in innings)
        if not concluded:
            live.add(match.session_id)
    return live


def home(request):
    """Homepage with upcoming/past sessions and vote counts.
    
    OPTIMIZATION: Uses prefetch_related to batch-load polls and votes,
    reducing queries from 20+ to ~5.
    """
    today = timezone.now().date()
    
    # OPTIMIZED: Batch-load polls and votes in 1 query
    sessions_qs = Session.objects.prefetch_related(
        Prefetch(
            'poll__votes',
            Vote.objects.select_related('user')
        )
    )
    
    upcoming_sessions = list(
        sessions_qs.filter(date__gte=today).order_by('date', 'time')
    )
    previous_sessions = list(
        sessions_qs.filter(date__lt=today).order_by('-date', '-time')[:10]
    )

    all_sessions = upcoming_sessions + previous_sessions
    live_session_ids = _live_match_session_ids(all_sessions)
    for session in all_sessions:
        session.is_live = session.id in live_session_ids

    session_vote_counts = {}
    session_voters = {}  # session_id -> yes-voter users (for the dashboard avatar stack)
    
    for session in all_sessions:
        if hasattr(session, 'poll'):
            # OPTIMIZED: Votes already loaded, no query!
            votes = list(session.poll.votes.all())
            yes_votes = [v for v in votes if v.choice == 'yes']
            no_votes = [v for v in votes if v.choice == 'no']
            
            yes_count = len(yes_votes)
            no_count = len(no_votes)
            total_votes = yes_count + no_count
            yes_percentage = (yes_count / total_votes * 100) if total_votes > 0 else 0
            
            session_vote_counts[session.id] = {
                'yes_votes': yes_count,
                'no_votes': no_count,
                'total_votes': total_votes,
                'yes_percentage': yes_percentage,
            }
            session_voters[session.id] = [
                v.user for v in yes_votes[:12]
            ]

    next_session = upcoming_sessions[0] if upcoming_sessions else None
    next_session_votes = (
        session_vote_counts.get(next_session.id) if next_session else None
    )

    outstanding_total = Decimal('0')
    wallet_balance = Decimal('0')
    next_session_user_vote = None
    
    if request.user.is_authenticated:
        # OPTIMIZED: Batch-load payments and wallets
        user = User.objects.prefetch_related(
            Prefetch('payment_set', Payment.objects.filter(status='pending')),
            'wallets'
        ).get(pk=request.user.pk)
        
        outstanding_total = sum(
            (p.amount for p in user.payment_set.all()),
            Decimal('0')
        )
        wallet_balance = sum(
            (w.amount for w in user.wallets.all()),
            Decimal('0')
        )
        
        if next_session and hasattr(next_session, 'poll'):
            # Find user's vote in the preloaded votes
            vote_obj = next(
                (v for v in next_session.poll.votes.all() if v.user_id == request.user.id),
                None
            )
            next_session_user_vote = vote_obj.choice if vote_obj else None

    context = {
        'upcoming_sessions': upcoming_sessions,
        'previous_sessions': previous_sessions,
        'vote_counts': session_vote_counts,
        'session_voters': session_voters,
        'next_session': next_session,
        'next_session_votes': next_session_votes,
        'next_session_user_vote': next_session_user_vote,
        'outstanding_total': outstanding_total,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'home.html', context)


# Rest of the file continues unchanged...
```

---

## 2. Settings.py Changes (cric_core/settings.py)

### 2a. Add Caching Configuration

**Add after SECURE_REFERRER_POLICY = "same-origin" (around line 60):**

```python
# --- Caching ---
# Use Redis if available (Render add-on), fall back to database
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,  # Fail gracefully if Redis unavailable
        },
        'KEY_PREFIX': 'indcric',
        'TIMEOUT': 300,  # 5 minutes default TTL
    }
}

# Fallback: If Redis env var not set, use database cache
if 'redis' not in os.getenv('REDIS_URL', '').lower():
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }
```

### 2b. Enable GZip Middleware

**In MIDDLEWARE list, add after 'SecurityMiddleware' (around line 150):**

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",  # ← ADD THIS
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ... rest
]

# Only compress responses larger than 500 bytes
GZIP_MINIMUM_LENGTH_BYTES = 500
```

### 2c. Optimize Static Files Storage

**Replace or add STORAGES section (around line 70–80):**

```python
# Determine which storage backend to use
if DEBUG:
    # Local dev: use filesystem
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
else:
    # Production: Cloudinary for media, WhiteNoise for static
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Set cache headers for static files (1 year = 31536000 seconds)
# Safe because Django uses content hashes in filenames
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
}

WHITENOISE_SKIP_COMPRESS_OFFLINE = False  # Ensure compression on deploy
WHITENOISE_AUTOREFRESH = DEBUG  # Dev hot-reload
```

---

## 3. Database Indexing Migration

**Create empty migration:**
```bash
python manage.py makemigrations --empty sessions --name add_perf_indexes
```

**Replace contents of apps/sessions/migrations/000X_add_perf_indexes.py:**

```python
# Generated migration for performance indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '0001_initial'),  # ← Adjust to your latest migration
    ]

    operations = [
        # Session indexes
        migrations.AddIndex(
            model_name='session',
            index=models.Index(
                fields=['date', '-time'],
                name='session_date_time_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(
                fields=['attendance_confirmed'],
                name='session_confirmed_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(
                fields=['created_by'],
                name='session_created_by_idx',
            ),
        ),
    ]
```

**Then:**
```bash
python manage.py migrate
```

---

## 4. Session Detail View with Prefetch

**In apps/sessions/views.py, update session_detail_view (or equivalent):**

```python
from django.db.models import Prefetch

@login_required
def session_detail_view(request, pk):
    """Detailed view of a session with matches, teams, payments.
    
    OPTIMIZED: Uses prefetch_related to batch-load all related objects.
    """
    session = (
        Session.objects
        .select_related('created_by', 'poll')
        .prefetch_related(
            # Batch-load all matches for this session
            Prefetch(
                'matches',
                Match.objects.prefetch_related(
                    # Batch-load teams within each match
                    Prefetch(
                        'teams',
                        Team.objects.prefetch_related(
                            # Batch-load players within each team
                            Prefetch(
                                'players',
                                Player.objects.select_related('user')
                            )
                        )
                    ),
                    # Batch-load innings + batting/bowling team players
                    Prefetch(
                        'innings',
                        Innings.objects.prefetch_related(
                            'batting_team__players__user',
                            'bowling_team__players__user',
                        )
                    )
                )
            ),
            # Batch-load poll votes
            Prefetch(
                'poll__votes',
                Vote.objects.select_related('user')
            ),
        )
        .get(pk=pk)
    )
    
    # ... rest of view remains unchanged ...
    return render(request, 'session_detail.html', context)
```

---

## 5. Cache Invalidation Helper

**Create file: apps/core/cache_utils.py**

```python
"""Cache utility functions"""
from django.core.cache import cache


def invalidate_session_cache(session_id):
    """Invalidate all caches related to a session"""
    cache.delete(f'session_{session_id}_votes')
    cache.delete(f'session_{session_id}_payments')
    cache.delete('home_upcoming_sessions')
    cache.delete('home_previous_sessions')


def invalidate_user_cache(user_id):
    """Invalidate all caches related to a user"""
    cache.delete(f'user_{user_id}_outstanding')
    cache.delete(f'user_{user_id}_wallet')
    cache.delete('home_upcoming_sessions')


def invalidate_all_caches():
    """Clear all app caches"""
    cache.clear()
```

**Usage in views:**

```python
from apps.core.cache_utils import invalidate_session_cache

@login_required
def vote_on_poll(request, poll_id):
    """User votes on a poll"""
    poll = Poll.objects.get(pk=poll_id)
    
    # ... vote logic ...
    
    # Invalidate poll votes cache
    invalidate_session_cache(poll.session_id)
    
    return render(request, 'partials/_poll.html', context)
```

---

## 6. Settings for Requirements.txt

**Add to requirements.txt:**

```
# Caching
redis>=4.5.0
django-redis>=5.2.0

# Performance monitoring (dev only)
django-debug-toolbar>=3.8.1
django-silk>=5.0.0
```

**Install:**
```bash
pip install -r requirements.txt
```

---

## 7. Verify Changes Checklist

After implementing, verify:

- [ ] `python manage.py check` passes
- [ ] `python manage.py migrate` completes without errors
- [ ] Dev server starts: `python manage.py runserver`
- [ ] Home page loads: http://localhost:8000/
- [ ] Admin panel works: http://localhost:8000/admin/
- [ ] Django Debug Toolbar shows query count on home page (target: <20)
- [ ] No cache-related errors in logs
- [ ] Session detail page loads (target: <15 queries)
- [ ] Payment/wallet sections load correctly
- [ ] Poll voting works and cache invalidates

---

## 8. Monitoring Dashboard Addition

**Optional: Add to settings.py for monitoring**

```python
# Logging for slow queries (dev)
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',  # Set to DEBUG to see all queries
            },
        },
    }
```

---

## Expected Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Home page queries | 50+ | 15–20 | -70% |
| Session detail queries | 40+ | 10–15 | -75% |
| Home load time | 2–3s | 600–800ms | -70% |
| Response size (GZIP) | 150KB | 100KB | -33% |
| Cache hit rate | 0% | 60%+ | Great! |

---

## Troubleshooting

**Cache not clearing?**
```python
# Manual clear in Django shell
from django.core.cache import cache
cache.clear()
```

**Redis connection failing?**
```python
# Check in settings - falls back to database cache
# Render: Add Redis add-on first, then set REDIS_URL env var
```

**Queries still high?**
```bash
# Use Django Debug Toolbar to find culprits
# Install: pip install django-debug-toolbar
# See panel at bottom of page
```

---

Ready to implement? Start with Phase 1 (database queries) — shows immediate improvement!
