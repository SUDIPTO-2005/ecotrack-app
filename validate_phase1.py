"""
Standalone validation script for emission factor data and calculator service.
Run with: python validate_phase1.py (no Django or pytest needed)
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

# ── 1. JSON validation ────────────────────────────────────────────────────────
print("=== Validating JSON data files ===")

defra_path = Path("backend/emission_factors/data/defra_2023.json")
ipcc_path  = Path("backend/emission_factors/data/ipcc_ar6.json")

with defra_path.open() as f:
    defra = json.load(f)

with ipcc_path.open() as f:
    ipcc = json.load(f)

print(f"✓  DEFRA 2023: {len(defra['factors'])} factors loaded")
print(f"✓  IPCC AR6: {len(ipcc['factors'])} factors loaded")

# Check all required fields
required = ["factor_id", "category", "subcategory", "factor_value", "unit",
            "source", "source_url", "source_version", "effective_date"]
for rec in defra["factors"]:
    for field in required:
        assert field in rec, f"Missing '{field}' in {rec.get('factor_id', '?')}"
    assert rec["factor_value"] >= 0, f"Negative factor: {rec['factor_id']}"

print(f"✓  All {len(defra['factors'])} DEFRA records have required fields and non-negative values")

# ── 2. Loader validation ──────────────────────────────────────────────────────
print("\n=== Validating emission_factors.loader ===")

from emission_factors.loader import get_factor, get_factors_by_category, iter_all_factors

petrol = get_factor("transport.car.petrol.average.per_km", version="2023-v1")
assert petrol.factor_value == Decimal("0.17003"), f"Petrol factor wrong: {petrol.factor_value}"
print(f"✓  Petrol car: {petrol.factor_value} {petrol.unit}  (expected 0.17003)")

electric = get_factor("transport.car.electric.average.per_km", version="2023-v1")
assert electric.factor_value < petrol.factor_value
print(f"✓  EV ({electric.factor_value}) < Petrol ({petrol.factor_value})")

vegan = get_factor("diet.vegan.per_day", version="2023-v1")
meat  = get_factor("diet.meat_heavy.per_day", version="2023-v1")
assert vegan.factor_value < meat.factor_value
print(f"✓  Vegan diet ({vegan.factor_value} kg/day) < Meat-heavy ({meat.factor_value} kg/day)")

india = get_factor("energy.electricity.india_grid.per_kwh", version="2023-v1")
uk    = get_factor("energy.electricity.uk_grid.per_kwh", version="2023-v1")
assert india.factor_value > uk.factor_value
print(f"✓  India grid ({india.factor_value}) > UK grid ({uk.factor_value}) kg CO2e/kWh")

# ── 3. Calculator service validation ─────────────────────────────────────────
print("\n=== Validating calculator_service ===")

from services.calculator_service import (
    CalculatorService, QuickCalculatorInput, DetailedCalculatorInput
)

svc = CalculatorService()

# Quick mode — annual, petrol car 200 km/week, meat-medium diet
result = svc.calculate_quick(QuickCalculatorInput(
    car_km_per_week=200,
    car_fuel_type="petrol",
    electricity_kwh_per_month=300,
    electricity_factor_id="energy.electricity.india_grid.per_kwh",
    diet_type="meat_medium",
    flights_short_haul_per_year=2,
    period_days=365,
))

print(f"✓  Quick mode result: {result.total_co2e_kg:.1f} kg CO2e ({result.total_co2e_tonnes:.2f} t)")
print(f"   Factor version: {result.factor_version}")
print(f"   Categories:")
for cat in result.categories:
    print(f"     {cat.category:15s}: {cat.co2e_kg:8.1f} kg  ({cat.percentage:.1f}%)")

pct_sum = sum(c.percentage for c in result.categories)
assert abs(pct_sum - Decimal("100")) < Decimal("1"), f"Percentages sum to {pct_sum}"
print(f"✓  Category percentages sum to ~100% ({pct_sum:.2f}%)")

# Annual projection
proj = result.annual_projection
assert proj.upper_bound_kg > proj.lower_bound_kg
assert proj.confidence_pct == Decimal("0.05")  # Full-year → ±5%
print(f"✓  Annual projection: {proj.lower_bound_tonnes:.2f}–{proj.upper_bound_tonnes:.2f} t CO2e (±{proj.confidence_pct*100:.0f}%)")

# 30-day snapshot → ±25%
result_30 = svc.calculate_quick(QuickCalculatorInput(
    car_km_per_week=200,
    diet_type="meat_medium",
    period_days=30,
))
assert result_30.annual_projection.confidence_pct == Decimal("0.25")
print(f"✓  30-day snapshot: ±25% confidence interval (correct)")

# Detailed mode
detailed = svc.calculate_detailed(DetailedCalculatorInput(
    car_km_per_week=150,
    bus_km_per_week=30,
    rail_km_per_week=100,
    flights_long_haul_per_year=1,
    electricity_kwh_per_month=250,
    electricity_factor_id="energy.electricity.india_grid.per_kwh",
    natural_gas_kwh_per_month=80,
    diet_type="meat_low",
    new_clothing_items_per_year=15,
    new_electronics_smartphones_per_year=1,
    waste_kg_per_week=4,
    recycling_fraction=0.4,
    food_waste_kg_per_week=0.5,
    period_days=365,
))
assert detailed.total_co2e_kg > Decimal("0")
assert detailed.mode == "detailed"
print(f"✓  Detailed mode result: {detailed.total_co2e_kg:.1f} kg CO2e")

print("\n🎉  All Phase 1 validations passed!\n")
print("Factor dataset citation check:")
for rec in defra["factors"][:5]:
    print(f"  {rec['factor_id']}")
    print(f"    Source: {rec['source']}")
    print(f"    URL:    {rec['source_url']}")
