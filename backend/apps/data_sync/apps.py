"""Data sync app configuration."""
from django.apps import AppConfig


class DataSyncConfig(AppConfig):
    """Data sync app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.data_sync"
    verbose_name = "Government Data Sync"
