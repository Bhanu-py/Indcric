from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()


class Command(BaseCommand):
    help = 'Create UserConsent records for all existing users without one'

    def add_arguments(self, parser):
        parser.add_argument(
            '--accept-all',
            action='store_true',
            help='Auto-accept all consents for existing users (recommended for gradual rollout)',
        )

    def handle(self, *args, **options):
        accept_all = options.get('accept_all', False)
        
        # Get all users without consent records
        users_without_consent = User.objects.filter(gdpr_consent__isnull=True)
        count = users_without_consent.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ All users already have consent records'))
            return
        
        self.stdout.write(f'Creating UserConsent records for {count} existing users...')
        
        created_count = 0
        for user in users_without_consent:
            UserConsent.objects.create(
                user=user,
                privacy_policy_accepted=accept_all,
                terms_accepted=accept_all,
                whatsapp_accepted=accept_all,
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Successfully created {created_count} UserConsent records'
            )
        )
        
        if accept_all:
            self.stdout.write(
                self.style.WARNING(
                    '⚠ Consents auto-accepted for all users. '
                    'Show login modal to let them review and explicitly accept if needed.'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    '⚠ Consents NOT accepted. Users will see modal on next login to accept terms.'
                )
            )
