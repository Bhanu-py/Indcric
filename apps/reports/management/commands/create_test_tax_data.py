"""Management command to create test data for tax compliance reports."""

from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.sessions.models import Session, SessionPlayer, Attendance
from apps.matches.models import Match, Team, Player
from apps.payments.models import Payment
from apps.donations.models import Donation, DonationCampaign

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for tax compliance reports (3 months)'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...')
        
        # Create users if they don't exist
        users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                username=f'player{i}',
                defaults={
                    'first_name': f'Player',
                    'last_name': f'{i}',
                    'email': f'player{i}@indcric.club',
                }
            )
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'Created/Found {len(users)} users'))
        
        # Create donation campaign
        campaign, _ = DonationCampaign.objects.get_or_create(
            title='General Donations',
            defaults={
                'blurb': 'Support IndCric Club operations',
                'is_active': True,
                'is_default': True,
            }
        )
        
        # Create sessions for last 3 months
        today = timezone.now().date()
        start_date = today - timedelta(days=90)
        
        sessions_created = 0
        for i in range(12):  # 12 sessions over 3 months
            session_date = start_date + timedelta(days=i * 7)
            
            session, created = Session.objects.get_or_create(
                name=f'Cricket Session {i+1}',
                date=session_date,
                defaults={
                    'location': 'Topsporthal Gent',
                    'time': timezone.datetime.strptime('18:00', '%H:%M').time(),
                    'duration': 2,
                    'cost': Decimal('50.00'),
                    'cost_per_person': Decimal('10.00'),
                    'attendance_confirmed': True,
                    'created_by': users[0],
                }
            )
            
            if created:
                sessions_created += 1
                
                # Create match for this session
                match, _ = Match.objects.get_or_create(
                    session=session,
                    name=f'Match 1',
                )
                
                # Create teams
                team1, _ = Team.objects.get_or_create(
                    match=match,
                    name='Team A',
                )
                team2, _ = Team.objects.get_or_create(
                    match=match,
                    name='Team B',
                )
                
                # Add players to session
                for user in users:
                    sp, _ = SessionPlayer.objects.get_or_create(
                        session=session,
                        user=user,
                        defaults={'team': team1 if users.index(user) < 3 else team2}
                    )
                    
                    # Create attendance
                    Attendance.objects.get_or_create(
                        match_player=sp,
                        defaults={'attended': True}
                    )
                    
                    # Create payment
                    Payment.objects.get_or_create(
                        user=user,
                        session=session,
                        defaults={
                            'amount': Decimal('10.00'),
                            'status': 'paid' if users.index(user) % 2 == 0 else 'pending',
                            'method': 'cash' if users.index(user) % 2 == 0 else 'wallet',
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS(f'Created {sessions_created} sessions'))
        
        # Create donations
        donations_created = 0
        for i in range(6):
            donation_date = start_date + timedelta(days=i * 15)
            
            donation, created = Donation.objects.get_or_create(
                campaign=campaign,
                donor_name=f'Donor {i+1}',
                donated_on=donation_date,
                defaults={
                    'amount': Decimal('25.00') + Decimal(i * 5),
                    'source': 'manual' if i % 2 == 0 else 'bank',
                    'note': f'Donation for operations',
                }
            )
            
            if created:
                donations_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {donations_created} donations'))
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
