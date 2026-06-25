from django.contrib import admin
from .models import UserConsent


@admin.register(UserConsent)
class UserConsentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'privacy_policy_accepted',
        'terms_accepted',
        'whatsapp_accepted',
        'accepted_at',
    )
    list_filter = (
        'privacy_policy_accepted',
        'terms_accepted',
        'whatsapp_accepted',
        'accepted_at',
    )
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('accepted_at', 'ip_address', 'user')
    fields = (
        'user',
        'privacy_policy_accepted',
        'terms_accepted',
        'whatsapp_accepted',
        'accepted_version',
        'ip_address',
        'accepted_at',
    )

    def has_add_permission(self, request):
        """Prevent manual creation - created automatically on signup"""
        return False
