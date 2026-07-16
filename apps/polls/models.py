from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse


class Poll(models.Model):
    session = models.OneToOneField(
        'cric_sessions.Session',
        on_delete=models.CASCADE,
        related_name='poll',
    )
    question = models.CharField(max_length=255, default="Should this session be played?")
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Deleting a poll removes its activity-feed row (e.g. 'Poll opened').
    feed_events = GenericRelation('notifications.ActivityEvent')

    def __str__(self):
        return f"Poll for {self.session.name}"

    def get_absolute_url(self):
        return reverse('poll_detail', args=[self.pk])


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
        ('all', 'Both'),
        ('out', 'Not available'),
    )
    choice = models.CharField(max_length=3, choices=CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    # Withdrawing a vote (delete) removes its activity-feed row (#45).
    feed_events = GenericRelation('notifications.ActivityEvent')

    class Meta:
        unique_together = ('poll', 'user')

    @classmethod
    def normalize_choice(cls, choice):
        return (choice or '').strip().lower()

    @classmethod
    def label_for_choice(cls, choice):
        normalized = cls.normalize_choice(choice)
        return dict(cls.CHOICES).get(normalized, normalized.title())
