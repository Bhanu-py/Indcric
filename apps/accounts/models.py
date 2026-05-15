from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    role = models.CharField(max_length=20, default='batsman')
    batting_rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    bowling_rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    fielding_rating = models.DecimalField(
        max_digits=3, decimal_places=1, default=2.5,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    matches_played = models.PositiveIntegerField(default=0)
    runs_scored = models.PositiveIntegerField(default=0)
    wickets_taken = models.PositiveIntegerField(default=0)
    catches_taken = models.PositiveIntegerField(default=0)
    stumps_taken = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.username}"
