"""
Signal handlers for accounts app.
- Create UserConsent record for existing users who don't have one
- Check consent on login
"""
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.conf import settings
from apps.gdpr.models import UserConsent

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_user_consent_on_user_creation(sender, instance, created, **kwargs):
    """
    Create a UserConsent record when a new user is created.
    This is a safety net in case UserConsent creation fails during signup.
    """
    if created:
        UserConsent.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def check_consent_on_login(sender, request, user, **kwargs):
    """
    Check if user has accepted GDPR consent on login.
    Sets a flag to show consent modal if consent is incomplete.
    """
    try:
        consent = UserConsent.objects.get(user=user)
        # Flag for template: show consent modal if not all consents accepted
        if not consent.all_consents_accepted:
            request.session['show_consent_modal'] = True
    except UserConsent.DoesNotExist:
        # User doesn't have consent record - will be created by signal above
        # Force modal to show
        request.session['show_consent_modal'] = True


def ready():
    """Import signals when app is ready."""
    pass
