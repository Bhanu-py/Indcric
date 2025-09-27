from django.core.management.base import BaseCommand
from cric.models import User
import csv


class Command(BaseCommand):
    help = 'Seeds the database with initial users from a CSV file'

    def handle(self, *args, **kwargs):
        with open('initial_users.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Use create_user to ensure passwords are hashed
                User.objects.create_user(
                    username=row['username'],
                    password=row['password'],
                    email=row['email'],
                    role=row['email'],
                    is_staff=bool(int(row['is_staff']))
                )
        self.stdout.write(self.style.SUCCESS('Successfully seeded users.'))
