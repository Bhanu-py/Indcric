from django.db import models


class BotEvent(models.Model):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'
    DIRECTION_CHOICES = [(INBOUND, 'Inbound'), (OUTBOUND, 'Outbound')]

    wa_message_id = models.CharField(max_length=100, unique=True)
    phone = models.CharField(max_length=20)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bot_events',
    )
    action = models.CharField(max_length=50)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.direction} {self.action} from {self.phone} at {self.created_at:%Y-%m-%d %H:%M}"
