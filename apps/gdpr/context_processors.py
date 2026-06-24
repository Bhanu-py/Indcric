"""
Context processors for GDPR app.
Makes consent-related variables available in all templates.
"""


def gdpr_context(request):
    """Add GDPR context variables to all templates."""
    # Check if user needs to accept consent (new or incomplete)
    show_consent_modal = False
    
    if request.user.is_authenticated:
        from apps.gdpr.models import UserConsent
        try:
            consent = UserConsent.objects.get(user=request.user)
            # Show modal if not all consents accepted
            show_consent_modal = not consent.all_consents_accepted
        except UserConsent.DoesNotExist:
            # User has no consent record - show modal
            show_consent_modal = True
    
    # Also check session flag (set after login)
    if request.session.get('show_consent_modal', False):
        show_consent_modal = True
    
    context = {
        'show_consent_modal': show_consent_modal,
    }
    
    return context
