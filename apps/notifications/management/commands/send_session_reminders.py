from django.core.management.base import BaseCommand

from apps.notifications.services import send_session_reminders


class Command(BaseCommand):
    help = "Send WhatsApp reminders for upcoming sessions (24h, morning, 2h). Idempotent."

    def handle(self, *args, **options):
        counts = send_session_reminders()
        self.stdout.write(self.style.SUCCESS(f"Reminders sent: {counts}"))
