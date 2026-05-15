from django.db import models
from django.urls import reverse


class Session(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    duration = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=100)
    cost_per_person = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    attendance_confirmed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sessions',
    )

    def get_absolute_url(self):
        return reverse('session_detail', args=[self.pk])

    def __str__(self):
        return self.name


class SessionPlayer(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    # String ref avoids circular import: sessions → matches
    team = models.ForeignKey('matches.Team', on_delete=models.CASCADE)
    paid = models.BooleanField(default=False)

    class Meta:
        unique_together = [('session', 'user')]

    def __str__(self):
        return f"{self.user.username} in {self.session.name}"


class Attendance(models.Model):
    match_player = models.ForeignKey(SessionPlayer, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = [('match_player',)]
