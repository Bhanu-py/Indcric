from django.conf import settings

from .models import JerseyOrderWindow


def feature_flags(request):
    """Expose jersey feature-gate to all templates (nav link, home CTA)."""
    ordering_open = False
    ordering_deadline = ''
    if settings.JERSEY_ORDERING_ENABLED:
        try:
            ordering_open = JerseyOrderWindow.ordering_is_open()
            window = JerseyOrderWindow.current()
            if window and window.is_enabled and window.closes_at:
                ordering_deadline = window.closes_at_label()
        except Exception:
            # Keep base pages resilient if the jersey tables are not ready yet.
            ordering_open = True

    return {
        'jersey_ordering_enabled': settings.JERSEY_ORDERING_ENABLED,
        'jersey_ordering_open': ordering_open,
        'jersey_ordering_deadline': ordering_deadline,
    }
