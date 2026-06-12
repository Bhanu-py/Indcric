from django.core.management.base import BaseCommand

from apps.banking.services.importer import import_all_links


class Command(BaseCommand):
    help = (
        "Sync bank transactions from every active BankLink. Filters incoming "
        "credits whose reference contains 'ICG' and creates Donation rows. "
        "Idempotent — safe to run on a cron."
    )

    def handle(self, *args, **options):
        summary = import_all_links()
        self.stdout.write(self.style.SUCCESS(f"Import done: {summary}"))
