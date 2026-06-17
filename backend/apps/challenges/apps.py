"""Challenges app configuration."""
from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    """Challenges app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.challenges"
    verbose_name = "Community Challenges"
