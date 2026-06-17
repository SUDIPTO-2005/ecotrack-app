"""
Unit tests for the carbon calculator service.

These tests verify the correctness of emission factor math against
known-correct reference values. This is the most safety-critical
test suite in the codebase — incorrect emission factors directly
mislead users about their environmental impact.

Test design principles:
- All tests are pure math: no database, no HTTP, no Django.
- Reference values are hand-calculated from cited sources.
- Each test documents its source and expected value.
- Edge cases and zero-inputs are explicitly tested.
- Annual projection confidence interval logic is tested.
- Factor versioning is tested (calculations pin a specific version).

Run with::

    pytest tests/unit/test_calculator_service.py -v
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from services.calculator_service import (
    AnnualProjection,
    CalculatorService,
    DetailedCalculatorInput,
    FootprintResult,
    QuickCalculatorInput,
)
from emission_factors.loader import get_factor, get_factors_by_category


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def svc() -> CalculatorService:
    """Create a fresh CalculatorService for each test."""
    return CalculatorService()


@pytest.fixture
def default_quick_input() -> QuickCalculatorInput:
    """Minimal valid quick-mode input."""
    return QuickCalculatorInput(
        car_km_per_week=0,
        electricity_kwh_per_month=0,
        diet_type="vegetarian",
        flights_short_haul_per_year=0,
        flights_long_haul_per_year=0,
        period_days=365,
    )


# ---------------------------------------------------------------------------
# Emission factor loader tests
# ---------------------------------------------------------------------------


class TestEmissionFactorLoader:
    """Tests for the emission factor data loader.

    Verifies that real factor data loads correctly and values match
    the cited source documents.
    """

    def test_loads_defra_2023_factors(self) -> None:
        """DEFRA 2023 factors load without error."""
        factors = get_factors_by_category("transport", version="2023-v1")
        assert len(factors) > 0, "Should have at least one transport factor"

    def test_petrol_car_factor_matches_defra_2023(self) -> None:
        """
        Petrol car emission factor matches DEFRA/BEIS 2023 published value.

        Source: DEFRA Conversion Factors 2023, Freighting goods sheet,
        'Car — average' row: 0.17003 kg CO2e/km (average of small/medium/large).
        URL: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2023
        """
        factor = get_factor("transport.car.petrol.average.per_km", version="2023-v1")
        assert factor.factor_value == Decimal("0.17003"), (
            f"Expected DEFRA 2023 petrol car factor 0.17003, got {factor.factor_value}. "
            "If DEFRA updates this value, update the data file AND this test, citing the new source."
        )
        assert factor.unit == "kg_CO2e_per_km"
        assert "DEFRA" in factor.source or "BEIS" in factor.source

    def test_electric_car_factor_lower_than_petrol(self) -> None:
        """
        EV factor must be lower than petrol car (UK grid 2023).

        This is a sanity check: if the EV factor ever exceeds the petrol factor,
        something is wrong with the data.
        """
        petrol = get_factor("transport.car.petrol.average.per_km", version="2023-v1")
        electric = get_factor("transport.car.electric.average.per_km", version="2023-v1")
        assert electric.factor_value < petrol.factor_value, (
            "EV should have lower emissions than petrol car on UK 2023 grid. "
            f"Got EV={electric.factor_value}, petrol={petrol.factor_value}"
        )

    def test_vegan_diet_lower_than_meat_heavy(self) -> None:
        """
        Vegan diet must have lower emissions than meat-heavy diet.

        Source: Scarborough et al. (2023) Nature Food — vegan 1.57 kg/day vs
        meat-heavy 7.19 kg/day.
        """
        vegan = get_factor("diet.vegan.per_day", version="2023-v1")
        meat_heavy = get_factor("diet.meat_heavy.per_day", version="2023-v1")
        assert vegan.factor_value < meat_heavy.factor_value

    def test_vegan_diet_factor_value(self) -> None:
        """
        Vegan diet factor matches Scarborough et al. 2023 published value.

        Source: Scarborough, P. et al. (2023). Vegans, vegetarians, fish-eaters and meat-eaters
        in the UK show discrepant environmental impacts. Nature Food, 4, 565–574.
        doi:10.1038/s43016-023-00795-w
        Value: 1.57 kg CO2e/day
        """
        factor = get_factor("diet.vegan.per_day", version="2023-v1")
        assert factor.factor_value == Decimal("1.57"), (
            f"Expected Scarborough 2023 vegan factor 1.57, got {factor.factor_value}"
        )

    def test_all_factors_have_source_citation(self) -> None:
        """All emission factors must have a non-empty source citation and URL.

        This enforces the 'no arbitrary numbers' rule — every factor
        must trace back to a citable source.
        """
        from emission_factors.loader import iter_all_factors
        for record in iter_all_factors(version="2023-v1"):
            assert record.source, f"Factor {record.factor_id} has no source citation"
            assert record.source_url, f"Factor {record.factor_id} has no source URL"

    def test_missing_factor_raises_key_error(self) -> None:
        """Requesting a non-existent factor raises KeyError."""
        with pytest.raises(KeyError, match="not found"):
            get_factor("transport.flying_carpet.per_km", version="2023-v1")

    def test_factor_values_are_positive(self) -> None:
        """All emission factors must be non-negative."""
        from emission_factors.loader import iter_all_factors
        for record in iter_all_factors(version="2023-v1"):
            assert record.factor_value >= Decimal("0"), (
                f"Factor {record.factor_id} has negative value {record.factor_value}"
            )


# ---------------------------------------------------------------------------
# Quick calculator tests
# ---------------------------------------------------------------------------


class TestQuickCalculator:
    """Tests for quick-mode (5-question) carbon calculator."""

    def test_zero_inputs_returns_non_zero_result(self, svc: CalculatorService) -> None:
        """
        Even with all transport/energy inputs at zero, diet+consumption estimates
        are applied in quick mode, so total is > 0.
        """
        inputs = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            flights_short_haul_per_year=0,
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        assert result.total_co2e_kg > Decimal("0")

    def test_car_emissions_calculated_correctly(self, svc: CalculatorService) -> None:
        """
        Car emissions math: 200 km/week × 52 weeks × 0.17003 kg/km = ~1768.3 kg CO2e/year.

        Reference calculation:
        - 200 km/week × (365/7) weeks = 10,428.57 km/year
        - 10,428.57 × 0.17003 = 1,773.2 kg CO2e

        Source: DEFRA/BEIS 2023 petrol average 0.17003 kg CO2e/km.
        """
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            car_fuel_type="petrol",
            electricity_kwh_per_month=0,
            diet_type="vegan",  # control variable
            period_days=365,
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
        )
        result = svc.calculate_quick(inputs)
        transport_cat = result.get_category("transport")
        assert transport_cat is not None

        # Calculate expected: 200 km/week × (365/7) weeks × 0.17003
        expected_km = Decimal("200") * (Decimal("365") / Decimal("7"))
        expected_kg = expected_km * Decimal("0.17003")

        # Allow ±1 kg tolerance for Decimal rounding
        assert abs(transport_cat.co2e_kg - expected_kg) < Decimal("1.0"), (
            f"Car transport: expected ~{expected_kg:.1f} kg, got {transport_cat.co2e_kg} kg"
        )

    def test_electric_car_lower_than_petrol(self, svc: CalculatorService) -> None:
        """Electric car produces less CO2e than petrol car for same distance."""
        base = QuickCalculatorInput(
            car_km_per_week=300,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            period_days=365,
        )
        petrol_result = svc.calculate_quick(base)
        electric_result = svc.calculate_quick(
            QuickCalculatorInput(
                car_km_per_week=300,
                car_fuel_type="electric",
                electricity_kwh_per_month=0,
                diet_type="vegan",
                period_days=365,
            )
        )
        petrol_transport = petrol_result.get_category("transport")
        electric_transport = electric_result.get_category("transport")
        assert petrol_transport is not None and electric_transport is not None
        assert electric_transport.co2e_kg < petrol_transport.co2e_kg

    def test_diet_type_affects_result(self, svc: CalculatorService) -> None:
        """Higher-meat diets produce more CO2e than vegan diets."""
        inputs_vegan = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            period_days=365,
        )
        inputs_meat_heavy = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="meat_heavy",
            period_days=365,
        )
        vegan_result = svc.calculate_quick(inputs_vegan)
        meat_result = svc.calculate_quick(inputs_meat_heavy)

        vegan_diet = vegan_result.get_category("diet")
        meat_diet = meat_result.get_category("diet")
        assert vegan_diet is not None and meat_diet is not None
        assert meat_diet.co2e_kg > vegan_diet.co2e_kg

    def test_meat_heavy_diet_annual_value(self, svc: CalculatorService) -> None:
        """
        Meat-heavy diet annual emissions: 7.19 kg/day × 365 = 2624.35 kg CO2e.

        Source: Scarborough et al. (2023) Nature Food, 7.19 kg CO2e/day for
        meat-heavy (>100g meat/day) diet.
        """
        inputs = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="meat_heavy",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        diet_cat = result.get_category("diet")
        assert diet_cat is not None

        expected_kg = Decimal("7.19") * Decimal("365")  # 2624.35
        assert abs(diet_cat.co2e_kg - expected_kg) < Decimal("1.0"), (
            f"Meat-heavy diet: expected ~{expected_kg:.1f} kg, got {diet_cat.co2e_kg} kg"
        )

    def test_flights_zero_produces_zero_flight_transport(self, svc: CalculatorService) -> None:
        """No flights → no flight emissions."""
        inputs = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            flights_short_haul_per_year=0,
            flights_long_haul_per_year=0,
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        transport = result.get_category("transport")
        # Transport can be 0 in quick mode if no car or flights
        assert transport is not None
        assert transport.co2e_kg == Decimal("0")

    def test_short_haul_flight_emissions(self, svc: CalculatorService) -> None:
        """
        Short-haul flight emissions: 1 return trip × 2 legs × 1100 km × 0.15570 kg/km = 342.54 kg.

        Reference:
        - Average short-haul one-way distance: 1,100 km
        - Return trip = 2 legs
        - DEFRA 2023 economy short-haul factor: 0.15570 kg CO2e/km (incl. RFI 1.9x)
        """
        inputs = QuickCalculatorInput(
            car_km_per_week=0,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            flights_short_haul_per_year=1,
            flights_long_haul_per_year=0,
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        transport = result.get_category("transport")
        assert transport is not None

        expected_kg = Decimal("2") * Decimal("1100") * Decimal("0.15570")  # 342.54 kg
        assert abs(transport.co2e_kg - expected_kg) < Decimal("5.0"), (
            f"Short-haul flight: expected ~{expected_kg:.1f} kg, got {transport.co2e_kg} kg"
        )

    def test_category_percentages_sum_to_100(self, svc: CalculatorService) -> None:
        """Category percentages must sum to approximately 100%."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            electricity_kwh_per_month=300,
            diet_type="meat_medium",
            flights_short_haul_per_year=2,
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        total_pct = sum(cat.percentage for cat in result.categories)
        assert abs(total_pct - Decimal("100")) < Decimal("1.0"), (
            f"Category percentages sum to {total_pct}, expected ~100"
        )

    def test_result_has_all_five_categories(self, svc: CalculatorService) -> None:
        """Quick mode result must have transport, energy, diet, consumption, waste."""
        inputs = QuickCalculatorInput(
            car_km_per_week=100,
            electricity_kwh_per_month=200,
            diet_type="vegetarian",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        category_names = {cat.category for cat in result.categories}
        expected = {"transport", "energy", "diet", "consumption", "waste"}
        assert expected.issubset(category_names), (
            f"Missing categories: {expected - category_names}"
        )

    def test_factor_version_stored_in_result(self, svc: CalculatorService) -> None:
        """FootprintResult must store the factor version used."""
        inputs = QuickCalculatorInput(
            car_km_per_week=100,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            country_grid_version="2023-v1",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        assert result.factor_version == "2023-v1"

    def test_period_days_stored_in_result(self, svc: CalculatorService) -> None:
        """FootprintResult must store the period_days value."""
        inputs = QuickCalculatorInput(
            car_km_per_week=100,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            period_days=90,
        )
        result = svc.calculate_quick(inputs)
        assert result.period_days == 90


# ---------------------------------------------------------------------------
# Detailed calculator tests
# ---------------------------------------------------------------------------


class TestDetailedCalculator:
    """Tests for detailed-mode (20+ question) carbon calculator."""

    def test_detailed_mode_includes_all_inputs(self, svc: CalculatorService) -> None:
        """Detailed mode correctly integrates all input categories."""
        inputs = DetailedCalculatorInput(
            car_km_per_week=200,
            car_fuel_type="petrol",
            bus_km_per_week=50,
            rail_km_per_week=100,
            flights_short_haul_per_year=2,
            flights_long_haul_per_year=1,
            electricity_kwh_per_month=300,
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            natural_gas_kwh_per_month=100,
            diet_type="meat_medium",
            new_clothing_items_per_year=20,
            new_electronics_laptops_per_year=1,
            waste_kg_per_week=5,
            recycling_fraction=0.3,
            food_waste_kg_per_week=1,
            period_days=365,
        )
        result = svc.calculate_detailed(inputs)
        assert result.total_co2e_kg > Decimal("0")
        assert result.mode == "detailed"

    def test_bus_emissions_calculated_correctly(self, svc: CalculatorService) -> None:
        """
        Bus emissions: 50 km/week × (365/7) weeks × 0.10230 kg/km = 266.8 kg CO2e.

        Source: DEFRA/BEIS 2023 local bus average 0.10230 kg CO2e/passenger-km.
        """
        inputs = DetailedCalculatorInput(
            bus_km_per_week=50,
            diet_type="vegan",
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            period_days=365,
        )
        result = svc.calculate_detailed(inputs)
        transport = result.get_category("transport")
        assert transport is not None

        weeks = Decimal("365") / Decimal("7")
        expected_kg = Decimal("50") * weeks * Decimal("0.10230")
        assert abs(transport.co2e_kg - expected_kg) < Decimal("2.0"), (
            f"Bus emissions: expected ~{expected_kg:.1f} kg, got {transport.co2e_kg} kg"
        )

    def test_natural_gas_emissions(self, svc: CalculatorService) -> None:
        """
        Natural gas: 100 kWh/month × 12 months × 0.18281 kg/kWh = 219.4 kg CO2e.

        Source: DEFRA/BEIS 2023 natural gas 0.18281 kg CO2e/kWh.
        """
        inputs = DetailedCalculatorInput(
            natural_gas_kwh_per_month=100,
            diet_type="vegan",
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            period_days=365,
        )
        result = svc.calculate_detailed(inputs)
        energy = result.get_category("energy")
        assert energy is not None

        # 100 kWh/month × (365/30.44) months × 0.18281
        months = Decimal("365") / Decimal("30.44")
        expected_kg = Decimal("100") * months * Decimal("0.18281")
        assert abs(energy.co2e_kg - expected_kg) < Decimal("2.0"), (
            f"Natural gas: expected ~{expected_kg:.1f} kg, got {energy.co2e_kg} kg"
        )

    def test_recycling_reduces_waste_emissions(self, svc: CalculatorService) -> None:
        """Higher recycling fraction produces lower waste emissions."""
        base_inputs = dict(
            waste_kg_per_week=10,
            diet_type="vegan",
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            period_days=365,
        )
        low_recycle = svc.calculate_detailed(
            DetailedCalculatorInput(**base_inputs, recycling_fraction=0.0)
        )
        high_recycle = svc.calculate_detailed(
            DetailedCalculatorInput(**base_inputs, recycling_fraction=1.0)
        )
        low_waste = low_recycle.get_category("waste")
        high_waste = high_recycle.get_category("waste")
        assert low_waste is not None and high_waste is not None
        assert low_waste.co2e_kg > high_waste.co2e_kg

    def test_laptop_purchase_emissions(self, svc: CalculatorService) -> None:
        """
        Laptop purchase: 1 laptop × 338 kg CO2e = 338 kg CO2e/year.

        Source: Apple MacBook Pro 14" Environmental Product Declaration 2023,
        manufacturing + transport phase = ~338 kg CO2e.
        """
        inputs = DetailedCalculatorInput(
            new_electronics_laptops_per_year=1,
            diet_type="vegan",
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            period_days=365,
        )
        result = svc.calculate_detailed(inputs)
        consumption = result.get_category("consumption")
        assert consumption is not None

        expected_kg = Decimal("338")
        assert abs(consumption.co2e_kg - expected_kg) < Decimal("5.0"), (
            f"Laptop purchase: expected ~{expected_kg:.1f} kg, got {consumption.co2e_kg} kg"
        )


# ---------------------------------------------------------------------------
# Annual projection tests
# ---------------------------------------------------------------------------


class TestAnnualProjection:
    """Tests for the annual CO2e projection with confidence interval."""

    def test_full_year_data_gives_narrow_interval(self, svc: CalculatorService) -> None:
        """365-day data should give ±5% confidence interval."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            diet_type="meat_medium",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        projection = result.annual_projection
        assert projection.confidence_pct == Decimal("0.05"), (
            f"Full-year data should give 5% uncertainty, got {projection.confidence_pct}"
        )

    def test_one_month_data_gives_wide_interval(self, svc: CalculatorService) -> None:
        """30-day data should give ±25% confidence interval."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            diet_type="meat_medium",
            period_days=30,
        )
        result = svc.calculate_quick(inputs)
        projection = result.annual_projection
        assert projection.confidence_pct == Decimal("0.25"), (
            f"30-day data should give 25% uncertainty, got {projection.confidence_pct}"
        )

    def test_three_month_data_gives_20pct_interval(self, svc: CalculatorService) -> None:
        """90-day data should give ±20% confidence interval."""
        inputs = QuickCalculatorInput(
            car_km_per_week=100,
            diet_type="vegetarian",
            period_days=90,
        )
        result = svc.calculate_quick(inputs)
        assert result.annual_projection.confidence_pct == Decimal("0.20")

    def test_projection_point_estimate_is_linear_extrapolation(
        self, svc: CalculatorService
    ) -> None:
        """Annual projection point estimate = period_kg × 365 / period_days."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            electricity_kwh_per_month=0,
            diet_type="vegan",
            period_days=182,
        )
        result = svc.calculate_quick(inputs)
        proj = result.annual_projection

        # Point estimate should equal period total × 365/182
        expected_point = (
            result.total_co2e_kg * Decimal("365") / Decimal("182")
        ).quantize(Decimal("0.001"))
        assert abs(proj.point_estimate_kg - expected_point) < Decimal("1.0"), (
            f"Point estimate: expected ~{expected_point:.1f}, got {proj.point_estimate_kg}"
        )

    def test_upper_bound_exceeds_lower_bound(self, svc: CalculatorService) -> None:
        """Upper confidence bound must be greater than lower bound."""
        inputs = QuickCalculatorInput(
            car_km_per_week=150,
            diet_type="meat_heavy",
            period_days=90,
        )
        result = svc.calculate_quick(inputs)
        proj = result.annual_projection
        assert proj.upper_bound_kg > proj.lower_bound_kg

    def test_bounds_correctly_derived_from_uncertainty(
        self, svc: CalculatorService
    ) -> None:
        """Lower = point × (1 - uncertainty), Upper = point × (1 + uncertainty)."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            diet_type="vegetarian",
            period_days=90,  # → 20% uncertainty
        )
        result = svc.calculate_quick(inputs)
        proj = result.annual_projection

        expected_lower = proj.point_estimate_kg * Decimal("0.80")
        expected_upper = proj.point_estimate_kg * Decimal("1.20")

        assert abs(proj.lower_bound_kg - expected_lower) < Decimal("1.0")
        assert abs(proj.upper_bound_kg - expected_upper) < Decimal("1.0")

    def test_tonnes_properties_are_correctly_scaled(self, svc: CalculatorService) -> None:
        """Tonne properties must equal kg / 1000."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            diet_type="meat_heavy",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        proj = result.annual_projection

        assert proj.point_estimate_tonnes == proj.point_estimate_kg / Decimal("1000")
        assert proj.lower_bound_tonnes == proj.lower_bound_kg / Decimal("1000")
        assert proj.upper_bound_tonnes == proj.upper_bound_kg / Decimal("1000")

    def test_zero_period_days_handled_gracefully(self, svc: CalculatorService) -> None:
        """Zero period_days must not cause division by zero."""
        # _compute_annual_projection handles period_days <= 0 by defaulting to 365
        service = CalculatorService()
        projection = service._compute_annual_projection(Decimal("1000"), period_days=0)
        assert projection.point_estimate_kg == Decimal("1000")  # 1000 × 365/365


# ---------------------------------------------------------------------------
# FootprintResult helper tests
# ---------------------------------------------------------------------------


class TestFootprintResult:
    """Tests for FootprintResult helper methods."""

    def test_total_co2e_tonnes_property(self, svc: CalculatorService) -> None:
        """total_co2e_tonnes = total_co2e_kg / 1000."""
        inputs = QuickCalculatorInput(
            car_km_per_week=300,
            diet_type="meat_heavy",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        assert result.total_co2e_tonnes == result.total_co2e_kg / Decimal("1000")

    def test_get_category_returns_correct_category(self, svc: CalculatorService) -> None:
        """get_category() returns the correct CategoryResult."""
        inputs = QuickCalculatorInput(
            car_km_per_week=200,
            diet_type="vegetarian",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        transport = result.get_category("transport")
        assert transport is not None
        assert transport.category == "transport"

    def test_get_nonexistent_category_returns_none(self, svc: CalculatorService) -> None:
        """get_category() returns None for non-existent category."""
        inputs = QuickCalculatorInput(
            car_km_per_week=0,
            diet_type="vegan",
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        assert result.get_category("unicorn_category") is None

    def test_categories_sorted_by_co2e_descending(self, svc: CalculatorService) -> None:
        """Categories should be sorted by co2e_kg descending (largest first)."""
        inputs = QuickCalculatorInput(
            car_km_per_week=500,  # high transport
            electricity_kwh_per_month=100,
            diet_type="meat_heavy",
            flights_long_haul_per_year=3,
            period_days=365,
        )
        result = svc.calculate_quick(inputs)
        co2e_values = [cat.co2e_kg for cat in result.categories]
        assert co2e_values == sorted(co2e_values, reverse=True), (
            "Categories should be sorted by CO2e descending"
        )


# ---------------------------------------------------------------------------
# Edge case and robustness tests
# ---------------------------------------------------------------------------


class TestCalculatorEdgeCases:
    """Edge cases and robustness tests."""

    def test_extremely_large_inputs_do_not_crash(self, svc: CalculatorService) -> None:
        """Very large input values should not cause arithmetic errors."""
        inputs = DetailedCalculatorInput(
            car_km_per_week=10_000,
            flights_long_haul_per_year=100,
            electricity_kwh_per_month=10_000,
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            natural_gas_kwh_per_month=10_000,
            diet_type="meat_heavy",
            new_clothing_items_per_year=1000,
            new_electronics_laptops_per_year=50,
            waste_kg_per_week=1000,
            period_days=365,
        )
        result = svc.calculate_detailed(inputs)
        assert result.total_co2e_kg > Decimal("0")

    def test_recycling_fraction_clamped_to_zero_one(self, svc: CalculatorService) -> None:
        """Recycling fraction outside 0–1 range should not cause negative emissions."""
        inputs_over = DetailedCalculatorInput(
            waste_kg_per_week=10,
            recycling_fraction=1.5,  # Over 100%
            diet_type="vegan",
            electricity_factor_id="energy.electricity.india_grid.per_kwh",
            period_days=365,
        )
        result = svc.calculate_detailed(inputs_over)
        waste = result.get_category("waste")
        assert waste is not None
        assert waste.co2e_kg >= Decimal("0"), "Waste emissions must not be negative"

    def test_partial_year_totals_less_than_full_year(self, svc: CalculatorService) -> None:
        """90-day period should produce lower totals than 365-day period."""
        base = dict(
            car_km_per_week=200,
            electricity_kwh_per_month=300,
            diet_type="meat_medium",
        )
        full_year = svc.calculate_quick(QuickCalculatorInput(**base, period_days=365))
        partial = svc.calculate_quick(QuickCalculatorInput(**base, period_days=90))
        assert partial.total_co2e_kg < full_year.total_co2e_kg

    def test_india_grid_factor_higher_than_uk_grid(self, svc: CalculatorService) -> None:
        """
        India grid (0.708 kg CO2e/kWh) must be higher than UK grid (0.207 kg CO2e/kWh).

        This reflects real-world grid carbon intensity:
        - India CEA 2022-23: 0.708 kg CO2e/kWh
        - UK DEFRA 2023: 0.207 kg CO2e/kWh
        """
        india_factor = get_factor("energy.electricity.india_grid.per_kwh", version="2023-v1")
        uk_factor = get_factor("energy.electricity.uk_grid.per_kwh", version="2023-v1")
        assert india_factor.factor_value > uk_factor.factor_value, (
            f"India grid ({india_factor.factor_value}) should be > UK grid ({uk_factor.factor_value})"
        )

    def test_india_grid_electricity_value(self) -> None:
        """
        India grid factor matches CEA published value.

        Source: Central Electricity Authority, India — CO2 Baseline Database
        for the Indian Power Sector, User Guide Version 18.0 (2022-23).
        Value: 0.708 kg CO2e/kWh (national grid emission factor).
        URL: https://cea.nic.in/wp-content/uploads/baseline/2023/CO2_Baseline_Database_...
        """
        factor = get_factor("energy.electricity.india_grid.per_kwh", version="2023-v1")
        assert factor.factor_value == Decimal("0.70800"), (
            f"CEA India grid factor should be 0.70800, got {factor.factor_value}"
        )
