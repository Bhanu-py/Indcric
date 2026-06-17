from django.contrib.contenttypes.fields import GenericRelation
from django.db import models


class Payment(models.Model):
    # Deleting a payment removes its activity-feed row.
    feed_events = GenericRelation('notifications.ActivityEvent')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    session = models.ForeignKey('cric_sessions.Session', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, default='wallet')  # 'wallet' or 'cash'

    class Meta:
        unique_together = ('user', 'session')


class Wallet(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    date = models.DateField(auto_now_add=True)
