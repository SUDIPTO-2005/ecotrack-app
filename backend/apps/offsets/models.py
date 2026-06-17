"""
Data models for the offsets app (Phase 8).

Stores read-only metadata of carbon offset projects (informational mode only).
"""
from __future__ import annotations

from django.db import models


class OffsetProject(models.Model):
    """Carbon offset projects information retrieved from registry sandbox."""

    project_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    registry = models.CharField(
        max_length=50,
        help_text="e.g. 'Verra', 'Gold Standard', 'Patch.io'",
    )
    price_per_tonne_usd = models.DecimalField(max_digits=10, decimal_places=2)
    certification = models.CharField(
        max_length=100,
        help_text="e.g. 'VCS', 'GS', 'CCBS'",
    )
    project_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True, db_index=True)
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Offset Project"
        verbose_name_plural = "Offset Projects"
        ordering = ["price_per_tonne_usd"]

    def __str__(self) -> str:
        return f"{self.name} ({self.registry}) — ${self.price_per_tonne_usd}/t"
