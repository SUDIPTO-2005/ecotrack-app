"""
Data models for the data_sync app (Phase 4).

Stores synced national per-capita emission datasets (like Our World in Data).
"""
from __future__ import annotations

from django.db import models


class NationalAverageDataset(models.Model):
    """
    Dataset storing synced national per-capita averages.
    
    Used to compare individual carbon footprints against national/global averages.
    """

    country_code = models.CharField(
        max_length=2,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code.",
    )
    year = models.PositiveSmallIntegerField(
        db_index=True,
        help_text="The calendar year this data represents.",
    )
    per_capita_co2e_tonnes = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        help_text="Per capita emissions in metric tonnes CO2e.",
    )
    source = models.CharField(
        max_length=200,
        default="Our World in Data (OWID)",
    )
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "National Average Dataset"
        verbose_name_plural = "National Average Datasets"
        unique_together = [("country_code", "year")]
        ordering = ["-year", "country_code"]

    def __str__(self) -> str:
        return f"{self.country_code} ({self.year}): {self.per_capita_co2e_tonnes} tonnes/capita"
