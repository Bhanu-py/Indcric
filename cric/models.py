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
    session = models.ForeignKey('Session', on_delete=models.CASCADE)  # Link to Session
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, default='wallet')  # 'wallet' or 'cash'
    
    class Meta:
        unique_together = ('user', 'session')  # Ensure each user can only be paid once per session

class Wallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)

class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    matches_played = models.PositiveIntegerField(default=0)
    runs_scored = models.PositiveIntegerField(default=0)
    wickets_taken = models.PositiveIntegerField(default=0)
    catches_taken = models.PositiveIntegerField(default=0)
    stumps_taken = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.username}"

class MatchPlayer(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey('Team', on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.username} in {self.match.name}"

class Attendance(models.Model):
    match_player = models.ForeignKey(MatchPlayer, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True)
    class Meta:
        unique_together = [('match_player',)]

class Session(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    duration = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=100)
    # New fields:
    cost_per_person = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attendance_confirmed = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sessions')
    
    def get_absolute_url(self):
        return reverse('session_detail', args=[self.pk])

class Poll(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='poll')
    question = models.CharField(max_length=255, default="Should this session be played?")
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Poll for {self.session.name}"

    def get_absolute_url(self):
        return reverse('poll_detail', args=[self.pk])

class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
    )
    choice = models.CharField(max_length=3, choices=CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll', 'user')

class Match(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='matches', null=True)
    name = models.CharField(max_length=100)
    winner = models.ForeignKey('Team', on_delete=models.CASCADE, related_name='won_matches', null=True, blank=True)

    def __str__(self):
        return f"{self.name} in {self.session.name}"

class Team(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='captained_teams')

    def __str__(self):
        return self.name

class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    paid = models.BooleanField(default=False)
    role = models.CharField(max_length=20)
    
    class Meta:
        unique_together = [('user', 'team')]

    def __str__(self):
        return self.user.username