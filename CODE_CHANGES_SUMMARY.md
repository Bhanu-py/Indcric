# Code Changes Summary

## 1. Model Addition (models.py)

```python
class TemporaryScoringAccess(models.Model):
    """Temporary scoring access grant for a player on a specific session date."""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                           related_name='temporary_scoring_access')
    session = models.ForeignKey('cric_sessions.Session', on_delete=models.CASCADE,
                              related_name='temporary_scoring_access')
    granted_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='granted_scoring_access')
    granted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    reason = models.TextField(blank=True, default='')

    class Meta:
        unique_together = [('user', 'session')]
        ordering = ['-granted_at']

    @property
    def is_valid(self):
        from django.utils import timezone
        return self.is_active and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.user.username} - {self.session.name} (expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"
```

## 2. Permission Check Helper (views.py)

```python
def _can_score(request, match):
    """Check if user can score: staff OR has valid temporary access."""
    if request.user.is_staff:
        return True
    
    if match.session_id is None:
        return False
    
    access = TemporaryScoringAccess.objects.filter(
        user=request.user,
        session_id=match.session_id,
        is_active=True,
        expires_at__gt=timezone.now()
    ).exists()
    
    return access
```

## 3. Updated Permission Check (views.py)

```python
# OLD:
def _staff_or_redirect(request, match):
    if request.user.is_staff:
        return None
    messages.error(request, "Only staff can score matches.")
    return redirect('session_detail', session_id=match.session_id)

# NEW:
def _staff_or_redirect(request, match):
    if _can_score(request, match):
        return None
    messages.error(request, "Only staff or authorized players can score matches.")
    return redirect('session_detail', session_id=match.session_id)
```

## 4. Updated All Scoring Views (example)

```python
# OLD:
@login_required
def score_ball_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if not request.user.is_staff or request.method != 'POST':
        return _render_console(request, innings)
    # ... rest of function

# NEW:
@login_required
def score_ball_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if not _can_score(request, innings.match) or request.method != 'POST':
        return _render_console(request, innings)
    # ... rest of function
```

## 5. Admin Configuration (admin.py)

```python
@admin.register(TemporaryScoringAccess)
class TemporaryScoringAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'granted_by', 'expires_at', 'is_active', 'is_valid_display')
    list_filter = ('is_active', 'session__date', 'granted_at')
    search_fields = ('user__username', 'user__first_name', 'session__name')
    readonly_fields = ('granted_at', 'granted_by', 'is_valid')

    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['revoke_access', 'extend_access_one_hour']

    def revoke_access(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} access(es) revoked.')
    revoke_access.short_description = 'Revoke selected access'
```

## 6. Form for Granting Access (forms.py)

```python
class TemporaryScoringAccessForm(forms.ModelForm):
    DURATION_CHOICES = [
        (30, '30 minutes'),
        (60, '1 hour'),
        (120, '2 hours'),
        (180, '3 hours'),
        (300, '5 hours'),
        (0, 'Custom duration'),
    ]
    
    duration_minutes = forms.ChoiceField(choices=DURATION_CHOICES, initial=60)
    custom_duration_minutes = forms.IntegerField(min_value=1, max_value=1440, required=False)

    class Meta:
        model = TemporaryScoringAccess
        fields = ['user', 'session', 'reason']

    def clean(self):
        cleaned_data = super().clean()
        # ... validation logic
        cleaned_data['expires_at'] = timezone.now() + timedelta(minutes=duration_minutes)
        return cleaned_data

    def save(self, commit=True, granted_by=None):
        instance = super().save(commit=False)
        if granted_by:
            instance.granted_by = granted_by
        if commit:
            instance.save()
        return instance
```

## 7. Views for Managing Access (views.py)

```python
@login_required
def grant_scoring_access_view(request, session_id):
    """Grant temporary scoring access to a player."""
    from apps.sessions.models import Session
    from .forms import TemporaryScoringAccessForm
    
    if not request.user.is_staff:
        messages.error(request, 'Only staff can grant scoring access.')
        return redirect('home')
    
    session = get_object_or_404(Session, id=session_id)
    
    if request.method == 'POST':
        form = TemporaryScoringAccessForm(request.POST)
        if form.is_valid():
            access = form.save(commit=False, granted_by=request.user)
            access.expires_at = form.cleaned_data['expires_at']
            access.save()
            messages.success(request, f'✓ Granted access to {access.user.username}')
            return redirect('session_detail', session_id=session.id)
    else:
        form = TemporaryScoringAccessForm(initial={'session': session.id})
    
    return render(request, 'cric/pages/grant_scoring_access.html', {'form': form, 'session': session})


@login_required
def revoke_scoring_access_view(request, access_id):
    """Revoke temporary scoring access."""
    access = get_object_or_404(TemporaryScoringAccess, id=access_id)
    
    if not request.user.is_staff:
        messages.error(request, 'Only staff can revoke scoring access.')
        return redirect('home')
    
    if request.method == 'POST':
        access.is_active = False
        access.save(update_fields=['is_active'])
        messages.success(request, f'✓ Revoked {access.user.username}\'s access')
        return redirect('session_detail', session_id=access.session_id)
    
    return render(request, 'cric/pages/confirm_revoke_access.html', {'access': access})
```

## 8. Management Command (management/commands/revoke_expired_scoring_access.py)

```python
class Command(BaseCommand):
    help = 'Revoke all expired temporary scoring access'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be revoked without making changes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        expired_access = TemporaryScoringAccess.objects.filter(
            is_active=True,
            expires_at__lte=now
        )

        count = expired_access.count()

        if dry_run:
            self.stdout.write(f'[DRY RUN] Would revoke {count} access')
            for access in expired_access:
                self.stdout.write(f'  - {access.user.username} for {access.session.name}')
            return

        expired_access.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'Successfully revoked {count} expired access'))
```

## 9. Test Examples (tests.py)

```python
class TemporaryScoringAccessTests(MatchFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.staff_user = User.objects.create_user(username="staff", password="x", is_staff=True)
        self.player_user = User.objects.create_user(username="player", password="x")
        self.player_with_access = User.objects.create_user(username="player_access", password="x")
        
        self.access = TemporaryScoringAccess.objects.create(
            user=self.player_with_access,
            session=self.session,
            granted_by=self.staff_user,
            expires_at=timezone.now() + timezone.timedelta(hours=1),
            is_active=True
        )

    def test_staff_can_score(self):
        self.client.login(username="staff", password="x")
        response = self.client.get(reverse('match_score', args=[self.match.id]))
        self.assertNotEqual(response.status_code, 302)

    def test_player_with_valid_access_can_score(self):
        self.client.login(username="player_access", password="x")
        response = self.client.get(reverse('match_score', args=[self.match.id]))
        self.assertNotEqual(response.status_code, 302)

    def test_player_with_expired_access_cannot_score(self):
        self.access.expires_at = timezone.now() - timezone.timedelta(minutes=1)
        self.access.save()
        
        self.client.login(username="player_access", password="x")
        response = self.client.get(reverse('match_score', args=[self.match.id]))
        self.assertEqual(response.status_code, 302)
```

## Import Statements Added

```python
# In views.py
from django.utils import timezone
from .models import TemporaryScoringAccess

# In admin.py
from .models import TemporaryScoringAccess

# In forms.py
from django.utils import timezone
from datetime import timedelta
from .models import TemporaryScoringAccess

# In management command
from django.utils import timezone
from apps.matches.models import TemporaryScoringAccess
```

## Migration SQL (to be auto-generated)

```sql
CREATE TABLE matches_temporaryscoringaccess (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    session_id BIGINT NOT NULL,
    granted_by_id BIGINT,
    granted_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    reason LONGTEXT NOT NULL DEFAULT '',
    UNIQUE KEY user_id_session_id (user_id, session_id),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES accounts_user(id),
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES sessions_session(id),
    CONSTRAINT fk_granted_by FOREIGN KEY (granted_by_id) REFERENCES accounts_user(id) ON DELETE SET NULL,
    INDEX ix_is_active (is_active),
    INDEX ix_expires_at (expires_at),
    INDEX ix_session_id (session_id),
    INDEX ix_granted_at (granted_at)
);
```

---

**All code follows Django best practices and maintains backward compatibility.**
