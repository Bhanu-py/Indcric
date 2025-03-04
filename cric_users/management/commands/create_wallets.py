from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from cric_users.models import Wallet
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Create wallet records for users who don\'t have one'

    def handle(self, *args, **options):
        users_without_wallet = []
        
        # Find users without wallets
        for user in User.objects.all():
            if not Wallet.objects.filter(user=user).exists():
                users_without_wallet.append(user)
        
        self.stdout.write(f"Found {len(users_without_wallet)} users without wallets")
        
        # Create wallets with default amount
        for user in users_without_wallet:
            Wallet.objects.create(
                user=user,
                amount=Decimal('0.00'),
                status='active'
            )
            self.stdout.write(f"Created wallet for user: {user.username}")
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(users_without_wallet)} wallet records"))
