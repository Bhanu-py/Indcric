import csv
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with initial users from a CSV file'

    def handle(self, *args, **kwargs):
        with open('initial_users.csv', 'r') as file:
            reader = csv.DictReader(file)
            created_count = 0
            skipped_count = 0
            for row in reader:
                defaults = {
                    'email': row['email'],
                    'role': row['role'].lower(),
                    'is_staff': bool(int(row['is_staff'])),
                }
                for field in ('batting_rating', 'bowling_rating', 'fielding_rating'):
                    if row.get(field):
                        defaults[field] = Decimal(row[field])
                user, created = User.objects.get_or_create(
                    username=row['username'],
                    defaults=defaults,
                )
                if created:
                    user.set_password(row['password'])
                    user.save()
                    created_count += 1
                else:
                    skipped_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created_count} created, {skipped_count} already existed.'
        ))
