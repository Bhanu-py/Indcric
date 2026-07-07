# IndCric — Performance Improvements & Missing Features Audit

**Date:** July 3, 2026  
**Status:** Comprehensive review of stage branch  
**Author:** GitHub Copilot  

---

## 🚀 PERFORMANCE IMPROVEMENTS NEEDED

### **1. DATABASE QUERY OPTIMIZATION (HIGH PRIORITY)**

#### Issue: N+1 Query Problem in Home View
**File:** `apps/sessions/views.py` (lines ~40–100)

**Current Problem:**
```python
for session in all_sessions:
    if hasattr(session, 'poll'):
        yes_qs = session.poll.votes.filter(choice='yes').select_related('user')
        # This fires a query PER session when poll is fetched
```

**Impact:** For 20 sessions on homepage, this causes 20+ database queries

**Fix:**
```python
# Use prefetch_related to batch-load polls and votes
all_sessions = (
    Session.objects
    .prefetch_related(
        Prefetch(
            'poll__votes',
            Vote.objects.filter(choice='yes').select_related('user')
        )
    )
    .order_by('date', 'time')
)
```

---

#### Issue: Missing select_related in Session Detail Views
**Files:** 
- `apps/sessions/views.py` (session_detail_view)
- `apps/matches/views.py` (team/scoring views)

**Current Problem:**
Each session displays related objects without batching:
- Session → created_by User
- Match → Team (multiple)
- Team → Players (multiple) → User
- Innings → batting/bowling teams

**Impact:** 50+ queries on a single match/session detail page

**Fix:**
```python
# In session_detail_view
session = (
    Session.objects
    .select_related('created_by', 'poll')
    .prefetch_related(
        Prefetch('matches', Match.objects.prefetch_related(
            'teams__players__user',
            'innings__batting_team__players__user',
            'innings__bowling_team__players__user',
        ))
    )
    .get(pk=pk)
)
```

---

#### Issue: Wallet & Payment Aggregations Missing select_related
**File:** `apps/sessions/views.py` (lines ~85–95)

**Current Problem:**
```python
outstanding_total = Payment.objects.filter(user=request.user, status='pending').aggregate(total=Sum('amount'))
wallet_balance = Wallet.objects.filter(user=request.user).aggregate(total=Sum('amount'))
# These queries run for EVERY authenticated user on home page
```

**Impact:** Extra 2–3 queries per page load

**Fix:**
```python
# Cache this for logged-in users, or fetch once per session
if request.user.is_authenticated:
    user = (
        User.objects
        .prefetch_related('payments', 'wallets')
        .get(pk=request.user.pk)
    )
    outstanding_total = sum(
        p.amount for p in user.payments.filter(status='pending')
    )
    wallet_balance = sum(p.amount for p in user.wallets.all())
```

---

### **2. CACHING STRATEGY (HIGH PRIORITY)**

**Current State:** No caching implemented (0 cache middleware)

**Recommended Setup:**

**Option A: Redis (Best for Production)**
```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'indcric',
        'TIMEOUT': 300,  # 5 minutes default
    }
}
```

**Option B: Database (No external dependency)**
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
# Then run: python manage.py createcachetable
```

**Where to Apply:**
- ✅ Home page (session lists, vote counts) — 5 min TTL
- ✅ Session detail polls — 1 min TTL  
- ✅ User profile stats — 10 min TTL
- ✅ Donation campaigns (rarely change) — 1 hour TTL

---

### **3. DATABASE INDEXING (MEDIUM PRIORITY)**

**Missing Indexes:**

```python
# apps/sessions/models.py
class Session(models.Model):
    date = models.DateField()  # ← ADD INDEX
    status = models.CharField(...)  # ← ADD IF EXISTS
    created_by = models.ForeignKey(...)  # ← HAS INDEX (FK)
    
    class Meta:
        indexes = [
            models.Index(fields=['date', '-time']),  # Common filter
            models.Index(fields=['created_by']),     # User's sessions
            models.Index(fields=['attendance_confirmed']),
        ]

# apps/polls/models.py
class Vote(models.Model):
    created_at = models.DateTimeField(...)  # ← MISSING INDEX
    
    class Meta:
        indexes = [
            models.Index(fields=['poll', 'user']),  # Unique constraint does this
            models.Index(fields=['created_at']),    # For recent votes
        ]

# apps/payments/models.py  
class Payment(models.Model):
    status = models.CharField(...)  # ← MISSING INDEX
    created_at = models.DateTimeField(...)  # ← MISSING INDEX
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['session']),
        ]
```

**Migration:**
```python
# apps/sessions/migrations/000X_add_indexes.py
from django.db import migrations, models

class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['date', '-time'], name='session_date_time_idx'),
        ),
        migrations.AddIndex(
            model_name='session',
            index=models.Index(fields=['attendance_confirmed'], name='session_confirmed_idx'),
        ),
    ]
```

---

### **4. FRONT-END OPTIMIZATION (MEDIUM PRIORITY)**

#### Missing Image Optimization
**File:** `apps/accounts/models.py` (avatar field)

**Problem:** User avatars uploaded to Cloudinary but no:
- Responsive image sizes
- WebP conversion
- Lazy loading attributes

**Fix:**
```html
<!-- In templates using avatars -->
{% if user.avatar %}
<img 
  src="{{ user.avatar.url }}?w=64&h=64&c=fill&q=auto&f=auto"
  srcset="
    {{ user.avatar.url }}?w=32&h=32&c=fill&q=auto&f=auto 32w,
    {{ user.avatar.url }}?w=64&h=64&c=fill&q=auto&f=auto 64w,
    {{ user.avatar.url }}?w=128&h=128&c=fill&q=auto&f=auto 128w
  "
  sizes="(max-width: 640px) 32px, 64px"
  loading="lazy"
  alt="{{ user.username }}"
/>
{% endif %}
```

---

#### Missing Static Asset Caching Headers
**File:** `cric_core/settings.py`

**Current:** WhiteNoise configured but no cache headers set

**Fix:**
```python
# settings.py
STORAGES = {
    'default': {...},  # Cloudinary
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    }
}

# In render.yaml or web server config
STATIC_URL_EXPIRES = 31536000  # 1 year — because Django uses hash-based filenames
```

---

### **5. API/RESPONSE OPTIMIZATION (MEDIUM PRIORITY)**

#### Missing HTMX Response Compression
**File:** Middleware chain in `settings.py`

**Current:** No GZip compression middleware

**Fix:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # ← ADD THIS
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... rest of middleware
]

# Tune compression
GZIP_MINIMUM_LENGTH_BYTES = 500  # Don't compress tiny responses
```

---

#### Missing Query String Optimization (HTMX Partials)
**Problem:** HTMX requests send full URL with query params even for partial updates

**Recommended Pattern:**
```python
# In view, detect HTMX requests
if request.htmx:
    # Return only the changed partial, skip layout
    return render(request, 'partials/_poll_votes.html', context)
else:
    # Return full page
    return render(request, 'pages/session_detail.html', context)
```

✅ **Already implemented** — good job!

---

### **6. DATABASE CONNECTION POOLING (LOW PRIORITY, PRODUCTION ONLY)**

**Current:** No connection pooling configured

**Fix for Render/Production:**
```python
# Install: pip install psycopg[binary,pool]
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,  # Reuse connections for 10 min
        conn_health_checks=True,  # Check connection health
    )
}
```

Or use PgBouncer on the database server.

---

---

## ✨ MISSING FEATURES

### **1. CONSENT VERSIONING & CHANGELOG (MEDIUM PRIORITY)**

**Status:** GDPR consent system is complete, but missing:

**Missing:**
- When privacy policy/terms change, old consents don't auto-invalidate
- No audit trail of *what* version users accepted
- No "re-accept if policy updated" flow

**Recommended:**
```python
# apps/gdpr/models.py
class UserConsent(models.Model):
    # ... existing fields ...
    privacy_policy_version = models.CharField(max_length=10, default='1.0')
    terms_version = models.CharField(max_length=10, default='1.0')
    
    class Meta:
        # Audit: one record per user + version combo
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'privacy_policy_version'],
                name='uniq_consent_per_version'
            ),
        ]

class PolicyVersion(models.Model):
    """Track policy changes — staff update this, triggers re-accept flow"""
    policy_type = models.CharField(
        max_length=20, 
        choices=[('privacy', 'Privacy'), ('terms', 'Terms')]
    )
    version = models.CharField(max_length=10)  # '1.1', '2.0', etc.
    content = models.TextField()
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
```

---

### **2. DATA PORTABILITY / EXPORT (MEDIUM PRIORITY)**

**Status:** Not implemented. GDPR requires this.

**Missing Feature:** "Download My Data" endpoint

**Recommended:**
```python
# apps/gdpr/views.py
@login_required
def data_export_view(request):
    """Return user's data as JSON (GDPR right to portability)"""
    if request.method == 'POST':
        user = request.user
        data = {
            'user': {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'created_at': user.date_joined.isoformat(),
            },
            'sessions': list(
                Session.objects.filter(created_by=user).values()
            ),
            'votes': list(
                Vote.objects.filter(user=user).values()
            ),
            'payments': list(
                Payment.objects.filter(user=user).values()
            ),
            'donations': list(
                Donation.objects.filter(user=user).values()
            ),
        }
        # Return as JSON download or email
        return JsonResponse(data)
    return render(request, 'gdpr/data_export.html')
```

---

### **3. ACTIVITY AUDIT LOG (MEDIUM PRIORITY)**

**Status:** Partial. `ActivityEvent` model exists but under-utilized.

**Missing:**
- User login/logout tracking
- Data modification timestamps (who changed what, when)
- Admin action audit trail

**Recommended:**
```python
# apps/notifications/models.py (expand existing ActivityEvent)
class ActivityEvent(models.Model):
    # Existing:
    # content_type, object_id, user, timestamp
    
    # Missing:
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('payment', 'Payment'),
        ('vote', 'Voted'),
    ]
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_values = models.JSONField(null=True, blank=True)  # Before change
    new_values = models.JSONField(null=True, blank=True)  # After change
    ip_address = models.GenericIPAddressField(null=True, blank=True)
```

**Usage:**
```python
# In views, log important actions
def payment_confirm_view(request, pk):
    payment = Payment.objects.get(pk=pk)
    old_status = payment.status
    payment.status = 'paid'
    payment.save()
    
    ActivityEvent.objects.create(
        user=request.user,
        action='update',
        content_type=ContentType.objects.get_for_model(Payment),
        object_id=payment.id,
        old_values={'status': old_status},
        new_values={'status': 'paid'},
        ip_address=get_client_ip(request),
    )
```

---

### **4. REAL-TIME NOTIFICATIONS (MEDIUM PRIORITY)**

**Status:** Not implemented. Site has WhatsApp bot but no in-app real-time updates.

**Missing:**
- Toast/alert when session is updated by another user
- Live poll vote count updates
- Payment status notifications

**Recommended Solution:**
Use **Django Channels** (WebSocket) or **Server-Sent Events (SSE)**

**Lightweight Option: SSE + HTMX**
```python
# apps/notifications/views.py
from django.http import StreamingHttpResponse

def notifications_stream(request):
    """SSE endpoint — stream events to client"""
    def event_generator():
        last_id = request.GET.get('last_id', 0)
        while True:
            events = ActivityEvent.objects.filter(
                id__gt=last_id,
                # Only relevant to this user (polls they voted on, sessions they attend, etc.)
            ).order_by('id')[:10]
            
            for event in events:
                yield f"data: {event.to_json()}\n\n"
                last_id = event.id
            
            time.sleep(2)  # Poll every 2 seconds
    
    return StreamingHttpResponse(
        event_generator(),
        content_type='text/event-stream'
    )
```

```html
<!-- In base.html -->
<script>
const sse = new EventSource('/api/notifications/stream/');
sse.addEventListener('message', (e) => {
    const event = JSON.parse(e.data);
    htmx.ajax('GET', `/session/${event.session_id}/poll/`, {
        target: `#poll-${event.session_id}`,
        swap: 'outerHTML'
    });
});
</script>
```

---

### **5. BATCH OPERATIONS / BULK ACTIONS (LOW PRIORITY)**

**Status:** Not implemented.

**Missing:**
- Bulk mark attendance for a session
- Bulk payment status update
- Bulk user role assignment

**Recommended:**
```python
# apps/sessions/views.py
@staff_member_required
def bulk_attendance_view(request, session_id):
    """Mark all non-attendees as confirmed at once"""
    if request.method == 'POST':
        session = Session.objects.get(pk=session_id)
        selected_ids = request.POST.getlist('player_ids')
        
        with transaction.atomic():
            Attendance.objects.filter(
                session=session,
                player_id__in=selected_ids
            ).update(status='confirmed')
        
        messages.success(request, f"Marked {len(selected_ids)} players as confirmed.")
        return redirect('session_detail', pk=session_id)
    
    # Show checkboxes for un-confirmed players
    return render(request, 'sessions/bulk_attendance.html', {...})
```

---

### **6. WALLET TOP-UP & TRANSACTIONS (MEDIUM PRIORITY)**

**Status:** Wallet model exists but interface incomplete.

**Missing:**
- UI to add funds to wallet
- Transaction history / statement
- Refund mechanism

**Recommended:**
```python
# apps/payments/models.py
class WalletTransaction(models.Model):
    """Ledger of wallet movements"""
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Can be negative (debit)
    TYPES = [('credit', 'Topup'), ('debit', 'Session'), ('refund', 'Refund')]
    type = models.CharField(max_length=10, choices=TYPES)
    related_session = models.ForeignKey('sessions.Session', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class WalletTopup(models.Model):
    """Track one top-up via Stripe/PayPal"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_intent_id = models.CharField(max_length=200)  # Stripe/PayPal ref
    status = models.CharField(max_length=20, default='pending')  # pending, completed, failed
    created_at = models.DateTimeField(auto_now_add=True)
```

**View:**
```python
# apps/payments/views.py
@login_required
def wallet_topup_view(request):
    """Render top-up form, then redirect to Stripe"""
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', '0'))
        if amount <= 0:
            messages.error(request, "Amount must be > 0.")
            return redirect('wallet_topup')
        
        # Create a pending top-up record
        topup = WalletTopup.objects.create(user=request.user, amount=amount)
        
        # Redirect to Stripe/PayPal
        return redirect(f'https://stripe.com/checkout/{topup.payment_intent_id}')
    
    return render(request, 'payments/wallet_topup.html')
```

---

### **7. EMAIL TEMPLATES & BRANDING (LOW PRIORITY)**

**Status:** Basic email setup exists but templates lack branding.

**Missing:**
- HTML email templates for all notifications
- Consistent branding (logo, colors, footer)
- Email preference center (opt-out)

**Recommended:**
```python
# Create apps/notifications/emails.py
def send_session_reminder_email(session, user):
    """Send pretty HTML email"""
    context = {
        'user': user,
        'session': session,
        'session_url': f"{settings.SITE_URL}/session/{session.id}/",
        'logo_url': f"{settings.SITE_URL}/static/logo.png",
    }
    
    html_message = render_to_string('emails/session_reminder.html', context)
    plain_message = render_to_string('emails/session_reminder.txt', context)
    
    send_mail(
        subject=f"Upcoming session: {session.name}",
        message=plain_message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
```

---

### **8. ANALYTICS DASHBOARD (LOW PRIORITY)**

**Status:** Not implemented.

**Missing:**
- Session attendance trends
- Revenue/wallet analytics
- Player stats (performance over time)
- Donation progress toward campaign goals

**Recommended:**
```python
# apps/notifications/views.py (or new apps/analytics/)
@staff_member_required
def analytics_dashboard_view(request):
    """Staff dashboard with charts"""
    sessions_count = Session.objects.filter(
        date__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    avg_attendance = (
        Session.objects
        .filter(attendance_confirmed=True)
        .annotate(
            attendance_count=Count('sessionplayer', filter=Q(sessionplayer__status='confirmed'))
        )
        .aggregate(avg=Avg('attendance_count'))
    )
    
    total_revenue = Payment.objects.filter(
        status='paid',
        created_at__gte=timezone.now() - timedelta(days=30)
    ).aggregate(total=Sum('amount'))
    
    return render(request, 'analytics/dashboard.html', {
        'sessions_count': sessions_count,
        'avg_attendance': avg_attendance['avg'] or 0,
        'total_revenue': total_revenue['total'] or 0,
    })
```

---

### **9. MOBILE APP / PUSH NOTIFICATIONS (LOW PRIORITY, FUTURE)**

**Status:** Not started. Site is mobile-responsive but not an app.

**Missing:**
- PWA manifest (partial — exists at `templates/manifest.webmanifest`)
- Service Worker push notifications
- Native app (iOS/Android)

**Recommended Start:**
```python
# Install package: pip install django-push-notifications
PUSH_NOTIFICATIONS_SETTINGS = {
    'FCM_API_KEY': os.getenv('FCM_API_KEY'),
}

# Send notification when session is created
from push_notifications.models import GCMDevice

def send_session_notification(session):
    devices = GCMDevice.objects.filter(user__is_active=True)
    devices.send_message(
        title=f"New session: {session.name}",
        body=f"On {session.date.strftime('%b %d')} at {session.time}",
    )
```

---

---

## 📋 IMPLEMENTATION PRIORITY MATRIX

| Feature | Priority | Effort | Impact | Timeline |
|---------|----------|--------|--------|----------|
| Database query optimization | 🔴 HIGH | 2–3 days | Performance +40% | Sprint 1 |
| Caching (Redis/DB) | 🔴 HIGH | 1–2 days | Performance +20% | Sprint 1 |
| Database indexing | 🟡 MEDIUM | 1 day | Performance +15% | Sprint 1 |
| Consent versioning | 🟡 MEDIUM | 2–3 days | GDPR compliance | Sprint 2 |
| Data portability (export) | 🟡 MEDIUM | 1–2 days | GDPR compliance | Sprint 2 |
| Activity audit log | 🟡 MEDIUM | 2–3 days | Compliance + debugging | Sprint 2 |
| Real-time notifications | 🟡 MEDIUM | 3–4 days | UX improvement | Sprint 3 |
| Wallet top-up UI | 🟡 MEDIUM | 2–3 days | Revenue feature | Sprint 3 |
| Email templates | 🟢 LOW | 1–2 days | Branding | Sprint 3 |
| Analytics dashboard | 🟢 LOW | 2–3 days | Insights | Sprint 4 |
| Mobile PWA/push | 🟢 LOW | 3–5 days | Future phase | Q3 2026 |

---

## 🚦 QUICK WINS (Can Do This Week)

1. **Add `select_related` to home view** (30 min) → `-15 queries`
2. **Add `prefetch_related` for poll votes** (30 min) → `-10 queries`
3. **Enable GZip middleware** (10 min) → `-30% response size`
4. **Add database indexes** (1 hour + migration) → `-20% query time on filters`
5. **Cache home page for 5 min** (1 hour) → `-50 queries per unauthenticated hit`

**Estimated impact:** Load time ↓ 50–70%, database load ↓ 40%

---

## 📞 NEXT STEPS

1. **Pick top 3 performance items** from QUICK WINS above
2. **Create a branch** `perf/optimizations`
3. **Measure baseline** (Django Debug Toolbar or Silk middleware)
4. **Apply fixes** with before/after query counts
5. **PR → stage → master** when complete

Would you like me to implement any of these fixes?
