"""
Calculator app models for EcoTrack.

Core domain models for emission factor storage (versioned, auditable)
and user footprint calculation sessions.

Design decisions:
- EmissionFactor records are immutable once created — updates create new records.
- FootprintEntry stores the factor_version used so historical calculations
  are reproducible even after factor updates.
- All CO2e values stored in kg for consistency; displayed in tonnes in the API.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class EmissionFactorCategory(models.TextChoices):
    """Top-level categories for emission factors."""
    TRANSPORT = "transport", "Transport"
    ENERGY = "energy", "Energy"
    DIET = "diet", "Diet & Food"
    CONSUMPTION = "consumption", "Consumption & Shopping"
    WASTE = "waste", "Waste & Recycling"


class CalculatorMode(models.TextChoices):
    """Calculation modes: quick (5 questions) vs. detailed (20+ questions)."""
    QUICK = "quick", "Quick Estimate"
    DETAILED = "detailed", "Detailed Calculation"


class EmissionFactor(models.Model):
    """
    Versioned, auditable emission factor record.

    Each factor maps a human activity (e.g. "driving a petrol car 1 km")
    to a CO2-equivalent weight. Factors are immutable once created —
    to update a factor, create a new record with a new source_version.

    The factor_id field is a stable dot-notation identifier used in
    calculation logic (e.g. "transport.car.petrol.per_km").
    Source citation is mandatory — no arbitrary numbers.

    Database indexes:
    - (factor_id, source_version): lookup for calculation service
    - (category, is_active): filtering active factors by category
    """

    factor_id = models.CharField(
        max_length=200,
        db_index=True,
        help_text="Stable dot-notation identifier, e.g. 'transport.car.petrol.per_km'",
    )
    category = models.CharField(
        max_length=20,
        choices=EmissionFactorCategory.choices,
        db_index=True,
    )
    subcategory = models.CharField(
        max_length=100,
        help_text="Human-readable subcategory, e.g. 'Petrol car (average)",
    )
    factor_value = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Emission factor in the stated unit",
    )
    unit = models.CharField(
        max_length=50,
        help_text="e.g. 'kg_CO2e_per_km', 'kg_CO2e_per_kWh'",
    )
    source = models.CharField(
        max_length=300,
        help_text="Full citation, e.g. 'DEFRA/BEIS 2023 Conversion Factors for Company Reporting'",
    )
    source_url = models.URLField(
        help_text="Direct link to the source document or dataset",
    )
    source_version = models.CharField(
        max_length=50,
        help_text="Version string, e.g. '2023-v1'",
    )
    effective_date = models.DateField(
        help_text="Date from which this factor is considered current",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Only active factors are used in new calculations",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional context, assumptions, or regional applicability notes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Emission Factor"
        verbose_name_plural = "Emission Factors"
        indexes = [
            models.Index(fields=["factor_id", "source_version"], name="idx_factor_id_version"),
            models.Index(fields=["category", "is_active"], name="idx_factor_cat_active"),
        ]
        ordering = ["category", "factor_id", "-effective_date"]

    def __str__(self) -> str:
        return f"{self.factor_id} ({self.source_version}): {self.factor_value} {self.unit}"


class EmissionFactorChangelog(models.Model):
    """
    Audit log for emission factor changes.

    Records who changed what factor, when, and citing which source revision.
    Required for auditability — users and administrators can trace
    every calculation to the exact source data used.
    """

    factor = models.ForeignKey(
        EmissionFactor,
        on_delete=models.PROTECT,  # Never delete factors that have a changelog
        related_name="changelog_entries",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="factor_changes",
        help_text="Admin user who made this change",
    )
    old_factor_id = models.CharField(max_length=200, blank=True)
    old_value = models.DecimalField(
        max_digits=12, decimal_places=6, null=True, blank=True
    )
    new_value = models.DecimalField(max_digits=12, decimal_places=6)
    source_citation = models.TextField(
        help_text="Source document and section justifying this change",
    )
    change_reason = models.TextField(
        help_text="Why was this factor changed? e.g. 'Annual DEFRA update to 2023 figures'",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Emission Factor Changelog"
        verbose_name_plural = "Emission Factor Changelog Entries"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["factor", "-changed_at"], name="idx_changelog_factor_date"),
        ]

    def __str__(self) -> str:
        return f"Change to {self.factor.factor_id} at {self.changed_at:%Y-%m-%d %H:%M}"


class FootprintEntry(models.Model):
    """
    One complete carbon footprint calculation session.

    Stores the user's raw inputs, the computed total CO2e, and critically,
    the emission factor version used — so historical calculations are
    reproducible even after factor updates.

    raw_data stores the user's form inputs as JSON for audit purposes.
    This is not used for display; use FootprintCategory for breakdown.

    Database indexes:
    - (user, date): primary access pattern for dashboard history
    - (user, mode): filtering by calculation mode
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="footprint_entries",
        db_index=True,
    )
    date = models.DateField(
        db_index=True,
        help_text="Date this footprint data represents (not necessarily today)",
    )
    mode = models.CharField(
        max_length=10,
        choices=CalculatorMode.choices,
        default=CalculatorMode.QUICK,
    )
    total_co2e_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Total CO2-equivalent in kilograms",
    )
    factor_version = models.CharField(
        max_length=50,
        help_text="Emission factor source version used for this calculation, e.g. '2023-v1'",
    )
    raw_data = models.JSONField(
        help_text="Raw user inputs for audit/reproducibility. Not for display — use categories.",
    )
    period_days = models.PositiveSmallIntegerField(
        default=365,
        help_text="Number of days this entry represents (for partial-year handling)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Footprint Entry"
        verbose_name_plural = "Footprint Entries"
        indexes = [
            models.Index(fields=["user", "date"], name="idx_footprint_user_date"),
            models.Index(fields=["user", "mode"], name="idx_footprint_user_mode"),
            models.Index(fields=["user", "-created_at"], name="idx_footprint_user_created"),
        ]
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.user} — {self.date} ({self.mode}): {self.total_co2e_kg:.1f} kg CO2e"

    @property
    def total_co2e_tonnes(self) -> Decimal:
        """Return total CO2e in metric tonnes (the common display unit)."""
        return self.total_co2e_kg / Decimal("1000")

    @property
    def annualised_co2e_kg(self) -> Decimal:
        """Extrapolate to annual footprint based on period_days.

        NOTE: This is a simple linear extrapolation. The calculator service
        computes this with a confidence interval — this property is the
        point estimate only, for convenience.
        """
        if self.period_days == 0:
            return self.total_co2e_kg
        return self.total_co2e_kg * Decimal("365") / Decimal(str(self.period_days))


class FootprintCategory(models.Model):
    """
    Per-category CO2e breakdown for a FootprintEntry.

    One entry per top-level category (transport, energy, diet, etc.).
    Used for dashboard charts and the AI coach breakdown.

    Database index:
    - (entry, category): primary access for breakdown queries
    """

    entry = models.ForeignKey(
        FootprintEntry,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    category = models.CharField(
        max_length=20,
        choices=EmissionFactorCategory.choices,
    )
    co2e_kg = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="CO2-equivalent in kilograms for this category",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of total footprint",
    )
    sub_breakdown = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional finer-grained breakdown within this category",
    )

    class Meta:
        verbose_name = "Footprint Category"
        verbose_name_plural = "Footprint Categories"
        unique_together = [("entry", "category")]
        indexes = [
            models.Index(fields=["entry", "category"], name="idx_category_entry_cat"),
        ]
        ordering = ["-percentage"]

    def __str__(self) -> str:
        return f"{self.entry} — {self.get_category_display()}: {self.co2e_kg:.1f} kg CO2e ({self.percentage:.1f}%)"
