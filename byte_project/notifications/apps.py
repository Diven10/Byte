"""App configuration for the notifications app."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the Notifications app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notifications'

    def ready(self):
        import notifications.signals  # noqa: F401
