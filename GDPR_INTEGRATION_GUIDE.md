# GDPR Integration Guide

This guide shows how to integrate the newly created GDPR app into the existing Indcric application.

## Phase 1: Integrate Consent Modal (Immediate)

### Step 1: Update base.html
Add the consent modal include to `templates/base.html` (in the body, before closing tag):

```html
{% include 'gdpr/consent_modal.html' %}
```

### Step 2: Test Consent Modal
1. Login to the application
2. The consent modal should appear (if not using the same browser/localStorage)
3. Check all three boxes and click "Accept & Continue"
4. Modal should close and you should see a success message

## Phase 2: Integrate with Signup Flow (Recommended)

### Update signup view in `apps/accounts/views.py`
```python
from apps.gdpr.models import UserConsent
from apps.gdpr.forms import ConsentForm

# In your signup view after user creation:
def signup_view(request):
    # ... existing signup logic ...
    if request.method == 'POST':
        # ... create user ...
        
        # Create UserConsent record
        UserConsent.objects.create(
            user=new_user,
            privacy_policy_accepted=request.POST.get('privacy_policy_accepted') == 'on',
            terms_accepted=request.POST.get('terms_accepted') == 'on',
            whatsapp_accepted=request.POST.get('whatsapp_accepted') == 'on',
            ip_address=get_client_ip(request),
        )
```

### Update signup form/template
Add GDPR consent fields to signup form before submit button:
```html
<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" name="privacy_policy_accepted" id="privacyCheck" required>
  <label class="form-check-label" for="privacyCheck">
    I accept the <a href="{% url 'gdpr:privacy_policy' %}" target="_blank">Privacy Policy</a>
  </label>
</div>

<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" name="terms_accepted" id="termsCheck" required>
  <label class="form-check-label" for="termsCheck">
    I accept the <a href="{% url 'gdpr:terms_of_service' %}" target="_blank">Terms of Service</a>
  </label>
</div>

<div class="form-check mb-3">
  <input class="form-check-input" type="checkbox" name="whatsapp_accepted" id="whatsappCheck" required>
  <label class="form-check-label" for="whatsappCheck">
    I accept that WhatsApp is required to vote on polls
  </label>
</div>
```

## Phase 3: Add Account Deletion to Settings (Recommended)

### Update account settings template
Add a "Danger Zone" section in `templates/account/settings.html`:
```html
<div class="card border-danger mt-5">
  <div class="card-header bg-danger text-white">
    <h5 class="mb-0">⚠️ Danger Zone</h5>
  </div>
  <div class="card-body">
    <p>Need to delete your account? Be careful - this cannot be undone.</p>
    <a href="{% url 'gdpr:delete_account' %}" class="btn btn-danger">
      Delete My Account
    </a>
  </div>
</div>
```

## Phase 4: Add Phone Number Encryption (Optional but Recommended)

### Install django-fernet
```bash
pip install django-fernet
```

### Update User model in `apps/accounts/models.py`
```python
from django_fernet.fields import EncryptedField

class User(AbstractUser):
    # ... existing fields ...
    phone = EncryptedField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Encrypted phone number for WhatsApp"
    )
```

### Create and apply migration
```bash
python manage.py makemigrations accounts
python manage.py migrate accounts
```

## Phase 5: Login Consent Check (Optional)

### Update login signal in `apps/accounts/signals.py`
```python
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from apps.gdpr.models import UserConsent

@receiver(user_logged_in)
def check_consent_on_login(sender, request, user, **kwargs):
    """Check if user has accepted GDPR terms"""
    try:
        consent = UserConsent.objects.get(user=user)
        if not consent.all_consents_accepted:
            # Can add a message or flag to show modal
            request.session['show_consent_modal'] = True
    except UserConsent.DoesNotExist:
        # New user login - will see modal on base.html
        request.session['show_consent_modal'] = True
```

## Testing Checklist

- [ ] Consent modal appears on login
- [ ] All three checkboxes are required
- [ ] Form submission works via AJAX
- [ ] Privacy Policy link opens and displays correctly
- [ ] Terms of Service link opens and displays correctly
- [ ] Account deletion form shows at `/gdpr/account/delete/`
- [ ] Confirmation email is sent with valid token
- [ ] Email link navigates to confirmation page with correct user
- [ ] Final deletion button removes account from database
- [ ] Deleted user cannot login anymore
- [ ] Cascade delete removes all related data (votes, sessions, etc.)

## Database Commands

### View all UserConsent records
```bash
python manage.py shell
>>> from apps.gdpr.models import UserConsent
>>> UserConsent.objects.all()
```

### Check if user has accepted consent
```bash
python manage.py shell
>>> from apps.accounts.models import User
>>> from apps.gdpr.models import UserConsent
>>> user = User.objects.get(username='testuser')
>>> user.gdpr_consent.all_consents_accepted
```

### Create consent record manually
```bash
python manage.py shell
>>> from apps.accounts.models import User
>>> from apps.gdpr.models import UserConsent
>>> user = User.objects.get(username='testuser')
>>> UserConsent.objects.create(
...     user=user,
...     privacy_policy_accepted=True,
...     terms_accepted=True,
...     whatsapp_accepted=True,
... )
```

## Email Configuration

The app uses Django's email backend configured in `settings.py`:
- **Development**: Console backend (emails printed to console)
- **Production**: Brevo backend (via BREVO_API_KEY)

To test email in development:
```bash
python manage.py runserver
# Trigger account deletion
# Check console output for email content
```

## URL Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/gdpr/consent/accept/` | POST | Accept GDPR consent | Yes |
| `/gdpr/account/delete/` | GET, POST | Request account deletion | Yes |
| `/gdpr/account/delete/confirm/<uidb64>/<token>/` | GET, POST | Confirm deletion via email | No |
| `/gdpr/privacy-policy/` | GET | View privacy policy | No |
| `/gdpr/terms-of-service/` | GET | View terms of service | No |

## Troubleshooting

### Issue: Consent modal not appearing
**Solution**: Ensure `{% include 'gdpr/consent_modal.html' %}` is in base.html and browser localStorage is enabled

### Issue: Email not sending
**Solution**: 
- Check EMAIL_BACKEND in settings.py
- Verify DEFAULT_FROM_EMAIL is set
- In production, verify BREVO_API_KEY environment variable

### Issue: 404 error on legal links
**Solution**: Verify `gdpr` app is in INSTALLED_APPS and URLs are included in main urls.py

### Issue: UserConsent not created
**Solution**: Ensure user is created BEFORE attempting to access gdpr_consent relation

## Security Notes

1. **Token Expiration**: Account deletion tokens expire after 24 hours
2. **Email Verification**: Deletion requires email link validation
3. **Two-Step Confirmation**: Two separate checkboxes must be confirmed
4. **Cascade Delete**: All related user data is automatically deleted
5. **IP Address Logging**: Consent acceptance records client IP for audit trail

## GDPR Compliance Features

✅ Right to Access - Users can view their data
✅ Right to Erasure - Users can delete their account completely
✅ Consent Tracking - All consent acceptance is logged with timestamp
✅ Audit Trail - IP address and version tracking
✅ Legal Documentation - Privacy Policy and Terms of Service provided
✅ Secure Deletion - Cascade delete removes all related data
