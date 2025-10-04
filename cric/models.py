from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    # add role field that can take value only from 'batsman', 'bowler', 'allrounder' only
    role = models.CharField(max_length=20, default='batsman')
    # Add rating fields for batting, bowling, and fielding
    batting_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    bowling_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    fielding_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    pass


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(
        'Match', on_delete=models.CASCADE)  # Link to Match
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)
    method = models.CharField(
        max_length=20, default='wallet')  # 'wallet' or 'cash'

    class Meta:
        # Ensure each user can only be paid once per match
        unique_together = ('user', 'match')


class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)


class Attendance(models.Model):
    player = models.ForeignKey(
        'Player', on_delete=models.CASCADE)  # Changed to Player
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True)

    class Meta:
        unique_together = [('player', 'match')]


class Match(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    duration = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    time = models.TimeField()
    winner = models.ForeignKey(
        'Team', on_delete=models.CASCADE, related_name='winner', null=True, blank=True)
    location = models.CharField(max_length=100)
    # New fields:
    cost_per_person = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    attendance_confirmed = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('match_detail', args=[self.pk])


class Team(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='captain')

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)
    role = models.CharField(max_length=20)
    matches_played = models.PositiveIntegerField(default=0)
    runs_scored = models.PositiveIntegerField(default=0)
    wickets_taken = models.PositiveIntegerField(default=0)
    catches_taken = models.PositiveIntegerField(default=0)
    stumps_taken = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('user', 'team')]

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


class MonthlyPeriod(models.Model):
    """Represents a monthly period for tracking balances and attendance"""
    name = models.CharField(max_length=50, unique=True)  # e.g., "January 2024"
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name


class PlayerBalance(models.Model):
    """Tracks monthly balance for each player"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.ForeignKey(MonthlyPeriod, on_delete=models.CASCADE)
    previous_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    monthly_advance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    total_advance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('user', 'period')

    def calculate_balance(self):
        """Calculate balance based on total advance and match costs"""
        self.total_advance = self.previous_balance + self.monthly_advance

        if self.total_advance == 0:
            self.balance = 0
        else:
            # Calculate total costs from attended matches
            total_cost = 0
            attendances = EnhancedAttendance.objects.filter(
                user=self.user,
                match__date__gte=self.period.start_date,
                match__date__lte=self.period.end_date,
                status__in=['P', 'Y']  # Present or Yet to Pay
            )

            for attendance in attendances:
                if attendance.status == 'P':
                    total_cost += attendance.match.cost_per_person or 0

            self.balance = max(0, self.total_advance - total_cost)

        self.save()
        return self.balance

    def __str__(self):
        return f"{self.user.username} - {self.period.name}"


class EnhancedAttendance(models.Model):
    """Enhanced attendance model similar to R app functionality"""
    ATTENDANCE_CHOICES = [
        ('P', 'Present'),
        ('E', 'Excused Absence'),
        ('Y', 'Yet to Pay'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=1, choices=ATTENDANCE_CHOICES, default='E')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'match')

    def __str__(self):
        return f"{self.user.username} - {self.match.name} - {self.get_status_display()}"
