from django.db import models
from django.utils import timezone
from django.conf import settings


class UserConsent(models.Model):
    """
    Track GDPR consent for each user.
    Stores whether user has accepted privacy policy, terms, and WhatsApp usage.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gdpr_consent'
    )
    privacy_policy_accepted = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    whatsapp_accepted = models.BooleanField(
        default=False,
        help_text="User accepts WhatsApp is required for voting"
    )
    accepted_at = models.DateTimeField(auto_now_add=True)
    accepted_version = models.CharField(
        max_length=10,
        default='v1',
        help_text="Version of terms accepted"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when consent was given"
    )

    class Meta:
        verbose_name = "User Consent"
        verbose_name_plural = "User Consents"

    def __str__(self):
        return f"Consent for {self.user.username} - {self.accepted_at.strftime('%Y-%m-%d')}"

    @property
    def all_consents_accepted(self):
        """Check if all required consents have been given"""
        return (
            self.privacy_policy_accepted and
            self.terms_accepted and
            self.whatsapp_accepted
        )
