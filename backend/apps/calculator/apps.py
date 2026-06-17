"""Calculator app configuration."""
from django.apps import AppConfig


class CalculatorConfig(AppConfig):
    """Calculator app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.calculator"
    verbose_name = "Carbon Calculator"
