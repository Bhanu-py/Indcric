from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse


class Session(models.Model):
    PLAY_DAY_CHOICES = [
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    duration = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    date_option_1 = models.DateField(null=True, blank=True)
    date_option_2 = models.DateField(null=True, blank=True)
    final_play_day = models.CharField(max_length=10, choices=PLAY_DAY_CHOICES, null=True, blank=True)
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
    # Deleting a session also removes its activity-feed rows (no orphan entries
    # with dead 'View'/'Pay' links). GenericRelation is virtual — no migration.
    feed_events = GenericRelation('notifications.ActivityEvent')

    def get_absolute_url(self):
        return reverse('session_detail', args=[self.pk])

    @property
    def proposed_dates(self):
        return [date for date in (self.date_option_1, self.date_option_2) if date]

    @property
    def has_saturday_option(self):
        return bool(self.date_option_1)

    @property
    def has_sunday_option(self):
        return bool(self.date_option_2)

    @property
    def has_two_date_options(self):
        return self.has_saturday_option and self.has_sunday_option

    @property
    def single_play_day(self):
        if self.has_saturday_option and not self.has_sunday_option:
            return 'sat'
        if self.has_sunday_option and not self.has_saturday_option:
            return 'sun'
        if not self.has_two_date_options and self.date:
            return 'sun' if self.date.weekday() == 6 else 'sat'
        return None

    @property
    def final_play_day_label(self):
        return dict(self.PLAY_DAY_CHOICES).get(self.final_play_day, '')

    @property
    def single_play_day_label(self):
        return dict(self.PLAY_DAY_CHOICES).get(self.single_play_day, '')

    def __str__(self):
        return self.name


class SessionPlayer(models.Model):
    """A user's attendance record for a session.

    Rows are auto-created when someone votes Yes on the session's availability
    poll. Team assignment is optional — a user can be on the attendance roster
    without yet being placed on a team. Teams come from the Match layer later.
    """

    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    # String ref avoids circular import: sessions → matches.
    # Nullable: attendance/payments live at session level; team is informational.
    team = models.ForeignKey(
        'matches.Team',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    paid = models.BooleanField(default=False)

    class Meta:
        unique_together = [('session', 'user')]

    def __str__(self):
        return f"{self.user.username} in {self.session.name}"


class Attendance(models.Model):
    match_player = models.ForeignKey(SessionPlayer, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    cost_exempt = models.BooleanField(default=False)
    payment = models.ForeignKey(
        'payments.Payment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        unique_together = [('match_player',)]
