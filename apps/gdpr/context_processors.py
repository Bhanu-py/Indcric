"""
Context processors for GDPR app.
Makes consent-related variables available in all templates.
"""

import logging
logger = logging.getLogger(__name__)


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
            logger.info(f"[GDPR] User {request.user.username}: consent.all_consents_accepted={consent.all_consents_accepted}, show_modal={show_consent_modal}")
        except UserConsent.DoesNotExist:
            # User has no consent record - show modal
            show_consent_modal = True
            logger.warning(f"[GDPR] User {request.user.username}: NO CONSENT RECORD, showing modal")
    else:
        logger.debug(f"[GDPR] Unauthenticated user, no modal needed")
    
    # Also check session flag (set after login)
    if request.session.get('show_consent_modal', False):
        show_consent_modal = True
        logger.info(f"[GDPR] Session flag set for show_consent_modal, showing modal")
    
    context = {
        'show_consent_modal': show_consent_modal,
    }
    
    logger.info(f"[GDPR] Final context: show_consent_modal={show_consent_modal}")
    
    return context
