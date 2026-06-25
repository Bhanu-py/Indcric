"""
Management command to create UserConsent records for all existing users who don't have one.
This ensures all users, even those created before GDPR was implemented, can accept consent.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.gdpr.models import UserConsent

User = get_user_model()


class Command(BaseCommand):
    help = 'Create UserConsent records for all existing users who don\'t have one'

    def handle(self, *args, **options):
        # Get all users
        all_users = User.objects.all()
        created_count = 0
        already_exist_count = 0
        
        self.stdout.write(f'Processing {all_users.count()} users...')
        
        for user in all_users:
            try:
                # Try to get existing consent
                consent = UserConsent.objects.get(user=user)
                already_exist_count += 1
            except UserConsent.DoesNotExist:
                # Create new consent record for this user
                # Mark as not accepted so they see the modal on next login
                UserConsent.objects.create(
                    user=user,
                    privacy_policy_accepted=False,
                    terms_accepted=False,
                    whatsapp_accepted=False,
                )
                created_count += 1
                self.stdout.write(f'Created consent record for: {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nDone! Created {created_count} new consent records. '
                f'{already_exist_count} already existed.'
            )
        )
