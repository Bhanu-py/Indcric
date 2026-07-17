from django.conf import settings


def feature_flags(request):
    """Expose jersey feature-gate to all templates (nav link, home CTA)."""
    return {
        'jersey_ordering_enabled': settings.JERSEY_ORDERING_ENABLED,
    }
