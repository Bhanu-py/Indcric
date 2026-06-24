"""
Context processors for GDPR app.
Makes consent-related variables available in all templates.
"""


def gdpr_context(request):
    """Add GDPR context variables to all templates."""
    context = {
        'show_consent_modal': request.session.get('show_consent_modal', False),
    }
    # Clear the flag after reading it
    if 'show_consent_modal' in request.session:
        del request.session['show_consent_modal']
    return context
