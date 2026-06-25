"""
Management command to revoke expired temporary scoring access.

Usage:
    python manage.py revoke_expired_scoring_access
    
This command automatically marks all expired temporary scoring access as inactive.
Can be run via cron or Celery for periodic cleanup.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.matches.models import TemporaryScoringAccess


class Command(BaseCommand):
    help = 'Revoke all expired temporary scoring access'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be revoked without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()

        # Find all active access that has expired
        expired_access = TemporaryScoringAccess.objects.filter(
            is_active=True,
            expires_at__lte=now
        )

        count = expired_access.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired access found.'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY RUN] Would revoke {count} access:'))
            for access in expired_access:
                self.stdout.write(
                    f'  - {access.user.username} for {access.session.name} '
                    f'(expired at {access.expires_at.strftime("%Y-%m-%d %H:%M:%S")})'
                )
            return

        # Revoke the access
        expired_access.update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully revoked {count} expired access'
        ))

        # Log each revoked access
        for access in expired_access:
            self.stdout.write(
                f'  ✓ {access.user.username} - {access.session.name}'
            )
