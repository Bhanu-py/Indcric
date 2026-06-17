from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    label = "notifications"

    def ready(self):
        # Wire the activity-feed emitters (donation / session / poll / match /
        # payment) once the app registry is populated.
        from . import signals  # noqa: F401
