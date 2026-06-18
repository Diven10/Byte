"""Models for the notifications app."""

from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """Notification model for user activity alerts."""

    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('rating', 'Rating'),
    )

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sent_notifications'
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES
    )
    recipe = models.ForeignKey(
        'recipes.Recipe', on_delete=models.CASCADE,
        null=True, blank=True, related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender.username} → {self.recipient.username}: {self.message[:50]}'
