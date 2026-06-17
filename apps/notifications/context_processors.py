from .models import unread_count_for


def activity_unread(request):
    """Expose the activity-feed unread count to every template so the header
    bell can render its badge. Zero for anonymous visitors."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'activity_unread': 0}
    return {'activity_unread': unread_count_for(user)}
