"""
Carbon footprint calculator service for EcoTrack.

This module contains all business logic for converting user inputs into
CO2-equivalent footprint estimates. It is the most correctness-critical
module in the codebase — every calculation is traceable to a citable
emission factor with a pinned version.

Design principles:
- All inputs validated before entering calculation logic.
- Emission factors are fetched by stable ID + version; the version used
  is stored on every FootprintEntry so calculations are reproducible.
- Annual projection uses a confidence interval, not a single false-precision
  number — partial-year extrapolations carry inherent uncertainty.
- No database writes here — this service returns pure result objects;
  the view layer is responsible for persisting them.

Usage::

    from services.calculator_service import (
        CalculatorService,
        QuickCalculatorInput,
        DetailedCalculatorInput,
    )

    svc = CalculatorService()
    result = svc.calculate_quick(QuickCalculatorInput(
        car_km_per_week=200,
        electricity_kwh_per_month=300,
        diet_type="meat_medium",
        flights_per_year=2,
        period_days=365,
    ))
    print(result.total_co2e_kg)  # e.g. Decimal("5823.5")
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from emission_factors.loader import FactorRecord, get_factor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DietType = Literal[
    "meat_heavy",
    "meat_medium",
    "meat_low",
    "fish",
    "vegetarian",
    "vegan",
]

CarFuelType = Literal["petrol", "diesel", "hybrid", "electric"]

# ---------------------------------------------------------------------------
# Input dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuickCalculatorInput:
    """Input for the quick calculator mode (5 key questions).

    All distance/energy values are weekly or monthly averages as noted.
    ``period_days`` is how many days this snapshot represents — used for
    annual projection.
    """

    car_km_per_week: float
    """Weekly km driven by car. 0 if no car."""

    car_fuel_type: CarFuelType = "petrol"
    """Fuel type of primary vehicle."""

    electricity_kwh_per_month: float = 0.0
    """Monthly household electricity consumption in kWh."""

    diet_type: DietType = "meat_medium"
    """Diet category matching emission factor IDs."""

    flights_short_haul_per_year: int = 0
    """Number of short-haul (<3700 km) return flights per year."""

    flights_long_haul_per_year: int = 0
    """Number of long-haul (>3700 km) return flights per year."""

    country_grid_version: str = "2023-v1"
    """Emission factor version to use for electricity. Controls grid intensity."""

    electricity_factor_id: str = "energy.electricity.india_grid.per_kwh"
    """Specific electricity grid factor ID — set by frontend based on user's country."""

    period_days: int = 365
    """Days represented by this snapshot. For annual data, use 365."""


@dataclass(frozen=True)
class DetailedCalculatorInput:
    """Input for the detailed calculator mode (20+ questions).

    Extends QuickCalculatorInput with finer-grained transport,
    energy, consumption, and waste data.
    """

    # === Transport ===
    car_km_per_week: float = 0.0
    car_fuel_type: CarFuelType = "petrol"
    bus_km_per_week: float = 0.0
    rail_km_per_week: float = 0.0
    motorbike_km_per_week: float = 0.0
    flights_short_haul_per_year: int = 0
    flights_long_haul_per_year: int = 0

    # === Energy ===
    electricity_kwh_per_month: float = 0.0
    electricity_factor_id: str = "energy.electricity.india_grid.per_kwh"
    natural_gas_kwh_per_month: float = 0.0
    heating_oil_litres_per_year: float = 0.0

    # === Diet ===
    diet_type: DietType = "meat_medium"

    # === Consumption ===
    new_clothing_items_per_year: int = 0
    new_electronics_laptops_per_year: int = 0
    new_electronics_smartphones_per_year: int = 0

    # === Waste ===
    waste_kg_per_week: float = 0.0
    recycling_fraction: float = 0.3
    """Fraction of waste that is recycled (0.0–1.0)."""
    food_waste_kg_per_week: float = 0.0

    # === Meta ===
    factor_version: str = "2023-v1"
    period_days: int = 365


@dataclass(frozen=True)
class CategoryResult:
    """CO2e result for a single emission category."""

    category: str
    co2e_kg: Decimal
    percentage: Decimal
    sub_breakdown: dict[str, Decimal] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"{self.category}: {self.co2e_kg:.1f} kg CO2e ({self.percentage:.1f}%)"


@dataclass(frozen=True)
class AnnualProjection:
    """Projected annual CO2e with confidence interval.

    Partial-year data carries inherent uncertainty — we model this as a
    ±20% confidence interval for data covering less than 6 months,
    narrowing linearly to ±5% for full-year data.

    This is intentionally conservative (wide interval) rather than
    reporting a false-precision single number.
    """

    point_estimate_kg: Decimal
    """Central annual estimate in kg CO2e."""

    lower_bound_kg: Decimal
    """Lower bound of 90% confidence interval."""

    upper_bound_kg: Decimal
    """Upper bound of 90% confidence interval."""

    period_days: int
    """How many days of data this projection is based on."""

    confidence_pct: Decimal
    """Width of the interval as a fraction (e.g. Decimal('0.10') = ±10%)."""

    @property
    def lower_bound_tonnes(self) -> Decimal:
        """Lower bound in metric tonnes."""
        return self.lower_bound_kg / Decimal("1000")

    @property
    def upper_bound_tonnes(self) -> Decimal:
        """Upper bound in metric tonnes."""
        return self.upper_bound_kg / Decimal("1000")

    @property
    def point_estimate_tonnes(self) -> Decimal:
        """Point estimate in metric tonnes."""
        return self.point_estimate_kg / Decimal("1000")


@dataclass
class FootprintResult:
    """Complete result of a footprint calculation.

    Returned by CalculatorService; the view layer persists this into
    FootprintEntry + FootprintCategory models.
    """

    total_co2e_kg: Decimal
    """Total CO2-equivalent in kg."""

    categories: list[CategoryResult]
    """Per-category breakdown, sorted by co2e_kg descending."""

    factor_version: str
    """Emission factor version used for this calculation."""

    mode: Literal["quick", "detailed"]
    """Which calculator mode produced this result."""

    period_days: int
    """Days this footprint represents."""

    annual_projection: AnnualProjection
    """Projected annual footprint with confidence interval."""

    @property
    def total_co2e_tonnes(self) -> Decimal:
        """Total CO2e in metric tonnes."""
        return self.total_co2e_kg / Decimal("1000")

    def get_category(self, category: str) -> CategoryResult | None:
        """Get a specific category result by name."""
        for cat in self.categories:
            if cat.category == category:
                return cat
        return None


# ---------------------------------------------------------------------------
# Calculator Service
# ---------------------------------------------------------------------------


class CalculatorService:
    """Main carbon footprint calculator service.

    All emission math lives here. The service layer is deliberately
    isolated from Django models, views, and serializers so it can be
    unit-tested without a database.

    Typical usage::

        svc = CalculatorService()
        result = svc.calculate_quick(inputs)
        result = svc.calculate_detailed(inputs)
    """

    # Average short-haul flight distance (one-way km, used if no route specified)
    _SHORT_HAUL_AVERAGE_KM: float = 1_100.0
    # Average long-haul flight distance (one-way km)
    _LONG_HAUL_AVERAGE_KM: float = 6_500.0

    def calculate_quick(self, inputs: QuickCalculatorInput) -> FootprintResult:
        """Calculate footprint from quick-mode inputs (5 key questions).

        Args:
            inputs: Validated QuickCalculatorInput dataclass.

        Returns:
            FootprintResult with total, category breakdown, and annual projection.
        """
        logger.debug("Running quick calculator", extra={"factor_version": inputs.country_grid_version})

        version = inputs.country_grid_version
        category_totals: dict[str, Decimal] = {}

        # --- Transport ---
        transport_kg = self._calc_car(
            inputs.car_km_per_week,
            inputs.car_fuel_type,
            inputs.period_days,
            version,
        )
        transport_kg += self._calc_flights(
            inputs.flights_short_haul_per_year,
            inputs.flights_long_haul_per_year,
            inputs.period_days,
            version,
        )
        category_totals["transport"] = transport_kg

        # --- Energy ---
        energy_kg = self._calc_electricity(
            inputs.electricity_kwh_per_month,
            inputs.electricity_factor_id,
            inputs.period_days,
            version,
        )
        category_totals["energy"] = energy_kg

        # --- Diet ---
        diet_kg = self._calc_diet(inputs.diet_type, inputs.period_days, version)
        category_totals["diet"] = diet_kg

        # Quick mode: consumption and waste are estimated from averages
        # (not asked; we use global-average proxies and note this in the result)
        consumption_kg = self._estimate_consumption_quick(inputs.period_days)
        category_totals["consumption"] = consumption_kg

        waste_kg = self._estimate_waste_quick(inputs.period_days)
        category_totals["waste"] = waste_kg

        return self._build_result(category_totals, version, "quick", inputs.period_days)

    def calculate_detailed(self, inputs: DetailedCalculatorInput) -> FootprintResult:
        """Calculate footprint from detailed-mode inputs (20+ questions).

        Args:
            inputs: Validated DetailedCalculatorInput dataclass.

        Returns:
            FootprintResult with total, category breakdown, and annual projection.
        """
        logger.debug("Running detailed calculator", extra={"factor_version": inputs.factor_version})

        version = inputs.factor_version
        category_totals: dict[str, Decimal] = {}

        # --- Transport ---
        transport_kg = self._calc_car(
            inputs.car_km_per_week, inputs.car_fuel_type, inputs.period_days, version
        )
        transport_kg += self._calc_bus(inputs.bus_km_per_week, inputs.period_days, version)
        transport_kg += self._calc_rail(inputs.rail_km_per_week, inputs.period_days, version)
        transport_kg += self._calc_motorbike(inputs.motorbike_km_per_week, inputs.period_days, version)
        transport_kg += self._calc_flights(
            inputs.flights_short_haul_per_year,
            inputs.flights_long_haul_per_year,
            inputs.period_days,
            version,
        )
        category_totals["transport"] = transport_kg

        # --- Energy ---
        energy_kg = self._calc_electricity(
            inputs.electricity_kwh_per_month,
            inputs.electricity_factor_id,
            inputs.period_days,
            version,
        )
        energy_kg += self._calc_natural_gas(inputs.natural_gas_kwh_per_month, inputs.period_days, version)
        energy_kg += self._calc_heating_oil(inputs.heating_oil_litres_per_year, inputs.period_days, version)
        category_totals["energy"] = energy_kg

        # --- Diet ---
        category_totals["diet"] = self._calc_diet(inputs.diet_type, inputs.period_days, version)

        # --- Consumption ---
        consumption_kg = self._calc_clothing(inputs.new_clothing_items_per_year, inputs.period_days, version)
        consumption_kg += self._calc_laptops(inputs.new_electronics_laptops_per_year, inputs.period_days, version)
        consumption_kg += self._calc_smartphones(inputs.new_electronics_smartphones_per_year, inputs.period_days, version)
        category_totals["consumption"] = consumption_kg

        # --- Waste ---
        category_totals["waste"] = self._calc_waste(
            inputs.waste_kg_per_week,
            inputs.recycling_fraction,
            inputs.food_waste_kg_per_week,
            inputs.period_days,
            version,
        )

        return self._build_result(category_totals, version, "detailed", inputs.period_days)

    # ------------------------------------------------------------------
    # Per-category calculation helpers
    # ------------------------------------------------------------------

    def _calc_car(
        self,
        km_per_week: float,
        fuel_type: CarFuelType,
        period_days: int,
        version: str,
    ) -> Decimal:
        """Calculate car transport emissions.

        Args:
            km_per_week: Weekly distance driven by car.
            fuel_type: Fuel type ('petrol', 'diesel', 'hybrid', 'electric').
            period_days: Number of days in the period.
            version: Emission factor version.

        Returns:
            CO2e in kg for the period.
        """
        if km_per_week <= 0:
            return Decimal("0")

        factor_id = f"transport.car.{fuel_type}.average.per_km"
        factor = self._get_factor_safe(factor_id, version)
        if factor is None:
            # Fall back to petrol average if specific fuel type not found
            factor = self._get_factor_safe("transport.car.petrol.average.per_km", version)
        if factor is None:
            logger.warning("No car emission factor found; defaulting to 0", extra={"factor_id": factor_id})
            return Decimal("0")

        weeks = Decimal(str(period_days)) / Decimal("7")
        total_km = Decimal(str(km_per_week)) * weeks
        return (total_km * factor.factor_value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    def _calc_bus(self, km_per_week: float, period_days: int, version: str) -> Decimal:
        """Calculate local bus emissions."""
        if km_per_week <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("transport.bus.local.per_km", version)
        if factor is None:
            return Decimal("0")
        weeks = Decimal(str(period_days)) / Decimal("7")
        return (Decimal(str(km_per_week)) * weeks * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_rail(self, km_per_week: float, period_days: int, version: str) -> Decimal:
        """Calculate national rail emissions."""
        if km_per_week <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("transport.rail.national.per_km", version)
        if factor is None:
            return Decimal("0")
        weeks = Decimal(str(period_days)) / Decimal("7")
        return (Decimal(str(km_per_week)) * weeks * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_motorbike(self, km_per_week: float, period_days: int, version: str) -> Decimal:
        """Calculate motorbike emissions."""
        if km_per_week <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("transport.motorbike.average.per_km", version)
        if factor is None:
            return Decimal("0")
        weeks = Decimal(str(period_days)) / Decimal("7")
        return (Decimal(str(km_per_week)) * weeks * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_flights(
        self,
        short_haul_count: int,
        long_haul_count: int,
        period_days: int,
        version: str,
    ) -> Decimal:
        """Calculate flight emissions.

        Flights are per-year counts; we scale to the period_days.
        Uses average one-way km for short and long haul.
        Return trips are counted as 2x one-way flights.

        Args:
            short_haul_count: Number of short-haul return trips per year.
            long_haul_count: Number of long-haul return trips per year.
            period_days: Days in this period (for scaling annual counts).
            version: Factor version.

        Returns:
            CO2e in kg for the period.
        """
        total = Decimal("0")
        period_fraction = Decimal(str(period_days)) / Decimal("365")

        if short_haul_count > 0:
            factor = self._get_factor_safe("transport.flight.economy.short_haul.per_km", version)
            if factor is not None:
                # Return trip = 2 one-way legs
                total_km = Decimal(str(short_haul_count * 2)) * Decimal(str(self._SHORT_HAUL_AVERAGE_KM))
                total += total_km * factor.factor_value * period_fraction

        if long_haul_count > 0:
            factor = self._get_factor_safe("transport.flight.economy.long_haul.per_km", version)
            if factor is not None:
                total_km = Decimal(str(long_haul_count * 2)) * Decimal(str(self._LONG_HAUL_AVERAGE_KM))
                total += total_km * factor.factor_value * period_fraction

        return total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    def _calc_electricity(
        self,
        kwh_per_month: float,
        factor_id: str,
        period_days: int,
        version: str,
    ) -> Decimal:
        """Calculate electricity consumption emissions.

        Args:
            kwh_per_month: Monthly electricity consumption.
            factor_id: Grid-specific factor ID (set by frontend based on user country).
            period_days: Days in this period.
            version: Factor version (may differ from main version for custom grids).

        Returns:
            CO2e in kg for the period.
        """
        if kwh_per_month <= 0:
            return Decimal("0")

        # Try the specified factor_id first; fall back to world average
        factor = self._get_factor_safe(factor_id, version)
        if factor is None:
            logger.warning(
                "Electricity factor not found, falling back to world average",
                extra={"factor_id": factor_id},
            )
            factor = self._get_factor_safe("energy.electricity.world_average.per_kwh", version)
        if factor is None:
            return Decimal("0")

        months = Decimal(str(period_days)) / Decimal("30.44")  # Average days per month
        total_kwh = Decimal(str(kwh_per_month)) * months
        return (total_kwh * factor.factor_value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    def _calc_natural_gas(self, kwh_per_month: float, period_days: int, version: str) -> Decimal:
        """Calculate natural gas emissions."""
        if kwh_per_month <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("energy.natural_gas.per_kwh", version)
        if factor is None:
            return Decimal("0")
        months = Decimal(str(period_days)) / Decimal("30.44")
        return (Decimal(str(kwh_per_month)) * months * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_heating_oil(self, litres_per_year: float, period_days: int, version: str) -> Decimal:
        """Calculate heating oil emissions."""
        if litres_per_year <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("energy.heating_oil.per_litre", version)
        if factor is None:
            return Decimal("0")
        period_fraction = Decimal(str(period_days)) / Decimal("365")
        return (Decimal(str(litres_per_year)) * period_fraction * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_diet(self, diet_type: DietType, period_days: int, version: str) -> Decimal:
        """Calculate diet-related emissions.

        Diet factors are per-day; we multiply by period_days.

        Args:
            diet_type: One of the DietType literals.
            period_days: Days in the period.
            version: Factor version.

        Returns:
            CO2e in kg for the period.
        """
        factor_id = f"diet.{diet_type}.per_day"
        factor = self._get_factor_safe(factor_id, version)
        if factor is None:
            logger.warning("Diet factor not found", extra={"factor_id": factor_id})
            return Decimal("0")
        return (Decimal(str(period_days)) * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_clothing(self, items_per_year: int, period_days: int, version: str) -> Decimal:
        """Calculate clothing consumption emissions."""
        if items_per_year <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("consumption.clothing.new_item", version)
        if factor is None:
            return Decimal("0")
        period_fraction = Decimal(str(period_days)) / Decimal("365")
        return (Decimal(str(items_per_year)) * period_fraction * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_laptops(self, count_per_year: int, period_days: int, version: str) -> Decimal:
        """Calculate laptop purchase emissions."""
        if count_per_year <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("consumption.electronics.laptop", version)
        if factor is None:
            return Decimal("0")
        period_fraction = Decimal(str(period_days)) / Decimal("365")
        return (Decimal(str(count_per_year)) * period_fraction * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_smartphones(self, count_per_year: int, period_days: int, version: str) -> Decimal:
        """Calculate smartphone purchase emissions."""
        if count_per_year <= 0:
            return Decimal("0")
        factor = self._get_factor_safe("consumption.electronics.smartphone", version)
        if factor is None:
            return Decimal("0")
        period_fraction = Decimal(str(period_days)) / Decimal("365")
        return (Decimal(str(count_per_year)) * period_fraction * factor.factor_value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _calc_waste(
        self,
        waste_kg_per_week: float,
        recycling_fraction: float,
        food_waste_kg_per_week: float,
        period_days: int,
        version: str,
    ) -> Decimal:
        """Calculate waste-related emissions.

        Splits waste into landfill and recycled fractions; food waste handled separately.

        Args:
            waste_kg_per_week: Total general waste per week in kg.
            recycling_fraction: Fraction of general waste that is recycled (0.0–1.0).
            food_waste_kg_per_week: Food waste per week (assumed landfill unless composted).
            period_days: Days in the period.
            version: Factor version.

        Returns:
            CO2e in kg for the period.
        """
        weeks = Decimal(str(period_days)) / Decimal("7")
        total = Decimal("0")

        if waste_kg_per_week > 0:
            landfill_factor = self._get_factor_safe("waste.landfill.per_kg", version)
            recycling_factor = self._get_factor_safe("waste.recycling.per_kg", version)

            landfill_fraction = max(0.0, min(1.0, 1.0 - recycling_fraction))
            recycling_frac = max(0.0, min(1.0, recycling_fraction))

            total_waste_kg = Decimal(str(waste_kg_per_week)) * weeks

            if landfill_factor:
                total += total_waste_kg * Decimal(str(landfill_fraction)) * landfill_factor.factor_value
            if recycling_factor:
                total += total_waste_kg * Decimal(str(recycling_frac)) * recycling_factor.factor_value

        if food_waste_kg_per_week > 0:
            food_factor = self._get_factor_safe("waste.food_waste.per_kg", version)
            if food_factor:
                total += Decimal(str(food_waste_kg_per_week)) * weeks * food_factor.factor_value

        return total.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    # ------------------------------------------------------------------
    # Quick-mode estimation proxies (for unanswered categories)
    # ------------------------------------------------------------------

    def _estimate_consumption_quick(self, period_days: int) -> Decimal:
        """Estimate consumption emissions using global average proxy.

        Used in quick mode where consumption is not asked. The estimate
        is clearly flagged as approximate in the API response.

        Global average consumption footprint ~1200 kg CO2e/year.
        Source: IPCC AR6 WGIII Chapter 5 (demand-side mitigation).
        """
        annual_proxy_kg = Decimal("1200")  # kg/year global average
        return (annual_proxy_kg * Decimal(str(period_days)) / Decimal("365")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    def _estimate_waste_quick(self, period_days: int) -> Decimal:
        """Estimate waste emissions using global average proxy.

        Used in quick mode. Global average ~200 kg CO2e/year from waste.
        Source: IPCC AR6 WGIII Chapter 11 (cities, buildings, transport).
        """
        annual_proxy_kg = Decimal("200")  # kg/year global average
        return (annual_proxy_kg * Decimal(str(period_days)) / Decimal("365")).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    # ------------------------------------------------------------------
    # Result assembly
    # ------------------------------------------------------------------

    def _build_result(
        self,
        category_totals: dict[str, Decimal],
        version: str,
        mode: Literal["quick", "detailed"],
        period_days: int,
    ) -> FootprintResult:
        """Assemble category totals into a FootprintResult.

        Args:
            category_totals: Dict mapping category name to kg CO2e.
            version: Factor version used.
            mode: Calculator mode ('quick' or 'detailed').
            period_days: Days the calculation covers.

        Returns:
            Complete FootprintResult with breakdown and annual projection.
        """
        total_kg = sum(category_totals.values(), Decimal("0"))

        categories: list[CategoryResult] = []
        for cat_name, cat_kg in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
            pct = (
                (cat_kg / total_kg * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                if total_kg > 0
                else Decimal("0")
            )
            categories.append(
                CategoryResult(
                    category=cat_name,
                    co2e_kg=cat_kg,
                    percentage=pct,
                )
            )

        projection = self._compute_annual_projection(total_kg, period_days)

        logger.info(
            "Footprint calculated",
            extra={
                "mode": mode,
                "total_co2e_kg": float(total_kg),
                "factor_version": version,
                "period_days": period_days,
            },
        )

        return FootprintResult(
            total_co2e_kg=total_kg.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
            categories=categories,
            factor_version=version,
            mode=mode,
            period_days=period_days,
            annual_projection=projection,
        )

    def _compute_annual_projection(
        self, period_kg: Decimal, period_days: int
    ) -> AnnualProjection:
        """Compute annual CO2e projection with confidence interval.

        The confidence interval widens for short-period data:
        - ≤30 days: ±25% (very uncertain)
        - 31–90 days: ±20%
        - 91–180 days: ±15%
        - 181–270 days: ±10%
        - 271–365 days: ±5%

        This models seasonal variation and the uncertainty of extrapolating
        behaviour patterns from limited data. The interval is NOT a
        statistical confidence interval in the strict sense — it is a
        practical uncertainty band to avoid conveying false precision.

        Args:
            period_kg: Measured CO2e for the period.
            period_days: Number of days the period covers.

        Returns:
            AnnualProjection with point estimate and bounds.
        """
        if period_days <= 0:
            period_days = 365

        # Linear extrapolation to full year
        point_estimate = (period_kg * Decimal("365") / Decimal(str(period_days))).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        # Uncertainty band based on data completeness
        if period_days <= 30:
            uncertainty_pct = Decimal("0.25")
        elif period_days <= 90:
            uncertainty_pct = Decimal("0.20")
        elif period_days <= 180:
            uncertainty_pct = Decimal("0.15")
        elif period_days <= 270:
            uncertainty_pct = Decimal("0.10")
        else:
            uncertainty_pct = Decimal("0.05")

        lower = (point_estimate * (Decimal("1") - uncertainty_pct)).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )
        upper = (point_estimate * (Decimal("1") + uncertainty_pct)).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        return AnnualProjection(
            point_estimate_kg=point_estimate,
            lower_bound_kg=lower,
            upper_bound_kg=upper,
            period_days=period_days,
            confidence_pct=uncertainty_pct,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_factor_safe(self, factor_id: str, version: str) -> FactorRecord | None:
        """Get an emission factor, returning None if not found.

        Logs a warning on miss rather than raising, so a missing factor
        results in 0 contribution for that sub-category rather than
        crashing the entire calculation.

        Args:
            factor_id: Dot-notation factor ID.
            version: Source version.

        Returns:
            FactorRecord if found, None otherwise.
        """
        try:
            return get_factor(factor_id, version)
        except KeyError:
            logger.warning(
                "Emission factor not found",
                extra={"factor_id": factor_id, "version": version},
            )
            return None
