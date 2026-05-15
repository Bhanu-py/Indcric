from django.db import models


class Match(models.Model):
    # String ref avoids circular import: matches → sessions
    session = models.ForeignKey(
        'cric_sessions.Session',
        on_delete=models.CASCADE,
        related_name='matches',
        null=True,
    )
    name = models.CharField(max_length=100)
    winner = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        related_name='won_matches',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name} in {self.session.name}"


class Team(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='captained_teams',
    )
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    paid = models.BooleanField(default=False)
    role = models.CharField(max_length=20)

    class Meta:
        unique_together = [('user', 'team')]

    def __str__(self):
        return self.user.username
