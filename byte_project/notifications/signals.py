"""Signals and utility functions for the notifications app.

Notifications are created directly in interaction views (toggle_like,
add_comment, toggle_follow) using the create_notification utility below.
"""

from notifications.models import Notification


def create_notification(sender_user, recipient_user, notification_type, recipe=None, message=''):
    """Utility function to create a notification.

    Does not create notification if sender == recipient (no self-notifications).

    Args:
        sender_user: The User who triggered the notification.
        recipient_user: The User who receives the notification.
        notification_type: One of 'like', 'comment', 'follow', 'rating'.
        recipe: Optional Recipe instance related to the notification.
        message: The notification message text.

    Returns:
        The created Notification instance, or None if sender == recipient.
    """
    if sender_user == recipient_user:
        return None

    return Notification.objects.create(
        sender=sender_user,
        recipient=recipient_user,
        notification_type=notification_type,
        recipe=recipe,
        message=message,
    )
