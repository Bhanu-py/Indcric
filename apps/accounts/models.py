from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    # Empty by default so the post-signup onboarding view triggers for new
    # users. Existing rows backfilled with 'batsman' retain that value and
    # correctly skip onboarding.
    role = models.CharField(max_length=20, blank=True, default='')
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
    # Stored on Cloudinary in staging/prod (MediaCloudinaryStorage), on the local
    # filesystem in dev. django-cleanup deletes the old file on replace/remove.
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    @property
    def avatar_url(self):
        """Uploaded avatar URL, or a generated ui-avatars fallback (matching the
        initials placeholder used across the header / chips today)."""
        if self.avatar:
            return self.avatar.url
        return (
            f"https://ui-avatars.com/api/?name={self.username}"
            "&background=166534&color=fff&bold=true"
        )


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    matches_played = models.PositiveIntegerField(default=0)
    runs_scored = models.PositiveIntegerField(default=0)
    wickets_taken = models.PositiveIntegerField(default=0)
    catches_taken = models.PositiveIntegerField(default=0)
    stumps_taken = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Profile of {self.user.username}"
