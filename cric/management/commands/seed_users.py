from django.core.management.base import BaseCommand
from cric.models import User
import csv

class Command(BaseCommand):
    help = 'Seeds the database with initial users from a CSV file'

    def handle(self, *args, **kwargs):
        with open('initial_users.csv', 'r') as file:
            reader = csv.DictReader(file)
            created_count = 0
            skipped_count = 0
            for row in reader:
                user, created = User.objects.get_or_create(
                    username=row['username'],
                    defaults={
                        'email': row['email'],
                        'role': row['role'].lower(),
                        'is_staff': bool(int(row['is_staff'])),
                    }
                )
                if created:
                    user.set_password(row['password'])
                    user.save()
                    created_count += 1
                else:
                    skipped_count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Done: {created_count} created, {skipped_count} already existed.'))
