"""App configuration for the interactions app."""

from django.apps import AppConfig


class InteractionsConfig(AppConfig):
    """Configuration for the Social Interactions app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interactions'
    verbose_name = 'Social Interactions'
