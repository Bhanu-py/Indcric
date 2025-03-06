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
    match = models.ForeignKey('Match', on_delete=models.CASCADE)  # Link to Match
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, default='wallet')  # 'wallet' or 'cash'
    
    class Meta:
        unique_together = ('user', 'match')  # Ensure each user can only be paid once per match

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)

class Attendance(models.Model):
    player = models.ForeignKey('Player', on_delete=models.CASCADE)  # Changed to Player
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
    winner = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='winner', null=True, blank=True)
    location = models.CharField(max_length=100)
    # New fields:
    cost_per_person = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attendance_confirmed = models.BooleanField(default=False)
    
    def get_absolute_url(self):
        return reverse('match_detail', args=[self.pk])

class Team(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captain')

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
        return self.name