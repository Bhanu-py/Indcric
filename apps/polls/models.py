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
    )
    choice = models.CharField(max_length=3, choices=CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('poll', 'user')
