import os
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Reset the database and load initial data from users.csv'

    def handle(self, *args, **kwargs):
        # Drop the database
        db_path = os.path.join(os.path.dirname(__file__), '../../../db.sqlite3')
        if os.path.exists(db_path):
            os.remove(db_path)
            self.stdout.write(self.style.SUCCESS('Database dropped successfully'))

        # Run migrations
        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('Migrations applied successfully'))

        # Load initial data
        call_command('load_initial_data')
        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully'))
        
        # Create superuser
        call_command('createsuperuser', interactive=True)
        self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        
        
        
