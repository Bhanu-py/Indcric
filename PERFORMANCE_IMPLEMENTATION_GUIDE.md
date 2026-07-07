# Quick Start: Performance Optimization Implementation

**Goal:** Implement quick wins in 1–2 days, reduce query count by 40%, improve page load time.

---

## Phase 1: Database Query Optimization (2–3 hours)

### Step 1.1: Fix Home View (apps/sessions/views.py)

**Current problematic code (lines ~40–100):**
```python
# BAD: Poll fetched per session (N+1)
for session in all_sessions:
    if hasattr(session, 'poll'):
        yes_qs = session.poll.votes.filter(choice='yes').select_related('user')
```

**Replace with:**
```python
from django.db.models import Prefetch

# GOOD: Batch-load all polls and votes in 1 query
all_sessions = (
    Session.objects
    .filter(Q(date__gte=today) | Q(date__lt=today))  # Both upcoming + past
    .prefetch_related(
        Prefetch(
            'poll__votes',
            Vote.objects.select_related('user')
        )
    )
    .order_by('date', 'time')
)

# Then in context loop, iterate preloaded votes
for session in all_sessions:
    if hasattr(session, 'poll'):
        votes = session.poll.votes.all()  # Already loaded, no query!
        yes_qs = [v for v in votes if v.choice == 'yes']
        yes_votes = len(yes_qs)
        # ... rest of loop
```

---

### Step 1.2: Add select_related for Wallet & Payments

**In home view, around line 85–95:**

```python
# OLD
outstanding_total = Payment.objects.filter(user=request.user, status='pending').aggregate(total=Sum('amount')).get('total')
wallet_balance = Wallet.objects.filter(user=request.user).aggregate(total=Sum('amount')).get('total')

# NEW: Cache within request
if request.user.is_authenticated:
    user = User.objects.prefetch_related(
        Prefetch('payment_set', Payment.objects.filter(status='pending')),
        'wallets'
    ).get(pk=request.user.pk)
    
    outstanding_total = sum(p.amount for p in user.payment_set.all()) or Decimal('0')
    wallet_balance = sum(w.amount for w in user.wallets.all()) or Decimal('0')
```

**Expected improvement:** -2 queries per authenticated user

---

### Step 1.3: Fix Match/Scoring Detail Views

**File:** `apps/matches/views.py` or `apps/sessions/views.py` (session_detail_view)

**Add at the top:**
```python
from django.db.models import Prefetch

session = (
    Session.objects
    .select_related('created_by', 'poll__feed_events')
    .prefetch_related(
        Prefetch(
            'matches',
            Match.objects.prefetch_related(
                Prefetch(
                    'teams',
                    Team.objects.prefetch_related(
                        Prefetch(
                            'players',
                            Player.objects.select_related('user')
                        )
                    )
                ),
                'innings__batting_team__players__user',
                'innings__bowling_team__players__user',
            )
        ),
        'feed_events'
    )
    .get(pk=pk)
)
```

**Expected improvement:** -20 queries on session detail page

---

## Phase 2: Caching Setup (1–2 hours)

### Step 2.1: Choose Cache Backend

**Option A: Redis (Recommended for Production)**
```bash
pip install redis
# OR on Render: use Redis add-on
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}
```

**Option B: Database (No external dependency)**
```bash
python manage.py createcachetable
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
```

---

### Step 2.2: Cache Home Page

**In apps/sessions/views.py, modify home() function:**

```python
from django.views.decorators.cache import cache_page
from django.core.cache import cache

@cache_page(300)  # Cache for 5 minutes
def home(request):
    """Homepage with sessions and votes"""
    # ... existing code ...
    return render(request, 'home.html', context)

# OR for more control:

def home(request):
    cache_key = 'home_upcoming_sessions'
    upcoming_sessions = cache.get(cache_key)
    
    if upcoming_sessions is None:
        today = timezone.now().date()
        upcoming_sessions = list(
            Session.objects
            .filter(date__gte=today)
            .prefetch_related('poll__votes__user')  # From Step 1.1
            .order_by('date', 'time')
        )
        cache.set(cache_key, upcoming_sessions, 300)  # 5 min TTL
    
    # ... rest of view ...
```

**Expected improvement:** -50 queries per unauthenticated user (Render free tier will thank you!)

---

### Step 2.3: Cache Session Poll Votes

**In session detail view:**

```python
from django.core.cache import cache

def session_detail_view(request, pk):
    cache_key = f'session_{pk}_votes'
    vote_counts = cache.get(cache_key)
    
    if vote_counts is None:
        session = Session.objects.get(pk=pk)
        if hasattr(session, 'poll'):
            yes_count = session.poll.votes.filter(choice='yes').count()
            no_count = session.poll.votes.filter(choice='no').count()
            vote_counts = {'yes': yes_count, 'no': no_count}
            cache.set(cache_key, vote_counts, 60)  # 1 min TTL
    
    # Invalidate cache when a vote is posted
    # In the vote POST handler:
    cache.delete(f'session_{pk}_votes')
```

**Expected improvement:** -5 queries per session detail load

---

## Phase 3: Database Indexing (1 hour)

### Step 3.1: Create Migration

```bash
python manage.py makemigrations --empty sessions --name add_performance_indexes
```

**Edit** `apps/sessions/migrations/000X_add_performance_indexes.py`:

```python
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('sessions', '000Y_previous_migration'),  # Adjust to latest
    ]

    operations = [
        # Session indexes
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['date', '-time'], name='session_date_time_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['attendance_confirmed'], name='session_confirmed_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['created_by'], name='session_created_by_idx'),
        ),
    ]
```

### Step 3.2: Similar for Polls & Payments

```python
# apps/polls/migrations/000X_add_indexes.py
migrations.AddIndex(
    model_name='vote',
    index=models.Index(fields=['created_at'], name='vote_created_at_idx'),
),

# apps/payments/migrations/000X_add_indexes.py
migrations.AddIndex(
    model_name='payment',
    index=models.Index(fields=['user', 'status'], name='payment_user_status_idx'),
),
migrations.AddIndex(
    model_name='payment',
    index=models.Index(fields=['created_at'], name='payment_created_at_idx'),
),
```

### Step 3.3: Apply Migrations

```bash
python manage.py migrate
```

**Expected improvement:** -20% query time on filtered queries

---

## Phase 4: Middleware Optimization (30 minutes)

### Step 4.1: Enable GZip Compression

**In settings.py, MIDDLEWARE list, add after SecurityMiddleware:**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # ← ADD THIS
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... rest
]

GZIP_MINIMUM_LENGTH_BYTES = 500  # Don't compress tiny responses
```

**Expected improvement:** -30% response payload size

---

### Step 4.2: Optimize Static Files

**In render.yaml, ensure build command includes:**

```yaml
buildCommand: |
  pip install -r requirements.txt && \
  python manage.py collectstatic --noinput && \
  python manage.py compress --force && \
  python manage.py migrate --noinput
```

**In settings.py:**

```python
STORAGES = {
    'default': {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
}

# Cache static files for 1 year (Django uses content hash in filenames)
STATIC_URL_EXPIRES = 31536000
```

---

## Testing & Verification

### Measure Baseline (Before Changes)

```bash
# Install Django Debug Toolbar
pip install django-debug-toolbar

# Add to settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

# Add to cric_core/urls.py
from django.conf import settings
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
```

Then:
1. Open http://localhost:8000/ (dev server)
2. Check "Queries" panel at bottom-right → note total count
3. Check "Time" panel → note total time

### Measure After

Repeat above steps after implementing each phase.

**Target metrics:**
- Home page: 50+ queries → 15–20 queries ✅
- Session detail: 40+ queries → 10–15 queries ✅
- Load time: 2–3s → 500–800ms ✅

---

## Rollout Plan

1. **Create branch:** `git checkout -b perf/optimizations`
2. **Implement Phase 1** (queries) + test locally
3. **Implement Phase 2** (caching) + test locally
4. **Implement Phase 3** (indexes) + test locally
5. **Implement Phase 4** (middleware) + test locally
6. **Push to stage:** `git push origin perf/optimizations`
7. **Open PR** on GitHub with before/after metrics
8. **Merge to stage** → verify in stage env
9. **Merge to master** → deploy to Render

---

## Revert Plan (If Issues)

```bash
# If caching causes stale data:
git revert <caching-commits>

# If indexing causes issues:
python manage.py migrate <app> 000Y_prev_migration  # Rollback migration
git revert <indexing-commits>
```

---

## Questions?

- **Caching data stale?** → Adjust TTL or add manual cache.delete() in POST handlers
- **Indexes slowing inserts?** → They shouldn't; monitor with pg_stat_statements
- **Redis not available?** → Fall back to database cache backend
- **Need per-user caching?** → Use `cache_page(60, cache='default', key_prefix=request.user.id)`

Let's implement Phase 1 first — should show immediate improvement!
