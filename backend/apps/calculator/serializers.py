"""
DRF serializers for the calculator app (Phase 3).

Validates user inputs for quick and detailed calculator sessions
before handing off to the CalculatorService.
"""
from __future__ import annotations

from decimal import Decimal
from rest_framework import serializers

from .models import FootprintEntry, FootprintCategory, CalculatorMode


class QuickCalculatorInputSerializer(serializers.Serializer):
    """Serializer validating inputs for Quick Calculator Mode (5 questions)."""

    car_km_per_week = serializers.FloatField(min_value=0.0)
    car_fuel_type = serializers.ChoiceField(choices=["petrol", "diesel", "hybrid", "electric"], default="petrol")
    electricity_kwh_per_month = serializers.FloatField(min_value=0.0, default=0.0)
    diet_type = serializers.ChoiceField(
        choices=["meat_heavy", "meat_medium", "meat_low", "fish", "vegetarian", "vegan"],
        default="meat_medium"
    )
    flights_short_haul_per_year = serializers.IntegerField(min_value=0, default=0)
    flights_long_haul_per_year = serializers.IntegerField(min_value=0, default=0)
    country_grid_version = serializers.CharField(max_length=50, default="2023-v1")
    electricity_factor_id = serializers.CharField(max_length=200, default="energy.electricity.india_grid.per_kwh")
    period_days = serializers.IntegerField(min_value=1, max_value=366, default=365)
    date = serializers.DateField(required=False)


class DetailedCalculatorInputSerializer(serializers.Serializer):
    """Serializer validating inputs for Detailed Calculator Mode (20+ questions)."""

    car_km_per_week = serializers.FloatField(min_value=0.0, default=0.0)
    car_fuel_type = serializers.ChoiceField(choices=["petrol", "diesel", "hybrid", "electric"], default="petrol")
    bus_km_per_week = serializers.FloatField(min_value=0.0, default=0.0)
    rail_km_per_week = serializers.FloatField(min_value=0.0, default=0.0)
    motorbike_km_per_week = serializers.FloatField(min_value=0.0, default=0.0)
    flights_short_haul_per_year = serializers.IntegerField(min_value=0, default=0)
    flights_long_haul_per_year = serializers.IntegerField(min_value=0, default=0)

    electricity_kwh_per_month = serializers.FloatField(min_value=0.0, default=0.0)
    electricity_factor_id = serializers.CharField(max_length=200, default="energy.electricity.india_grid.per_kwh")
    natural_gas_kwh_per_month = serializers.FloatField(min_value=0.0, default=0.0)
    heating_oil_litres_per_year = serializers.FloatField(min_value=0.0, default=0.0)

    diet_type = serializers.ChoiceField(
        choices=["meat_heavy", "meat_medium", "meat_low", "fish", "vegetarian", "vegan"],
        default="meat_medium"
    )

    new_clothing_items_per_year = serializers.IntegerField(min_value=0, default=0)
    new_electronics_laptops_per_year = serializers.IntegerField(min_value=0, default=0)
    new_electronics_smartphones_per_year = serializers.IntegerField(min_value=0, default=0)

    waste_kg_per_week = serializers.FloatField(min_value=0.0, default=0.0)
    recycling_fraction = serializers.FloatField(min_value=0.0, max_value=1.0, default=0.3)
    food_waste_kg_per_week = serializers.FloatField(min_value=0.0, default=0.0)

    factor_version = serializers.CharField(max_length=50, default="2023-v1")
    period_days = serializers.IntegerField(min_value=1, max_value=366, default=365)
    date = serializers.DateField(required=False)


class CategoryBreakdownSerializer(serializers.ModelSerializer):
    """Serializer for FootprintCategory representation."""

    class Meta:
        model = FootprintCategory
        fields = ["category", "co2e_kg", "percentage", "sub_breakdown"]


class AnnualProjectionSerializer(serializers.Serializer):
    """Serializer representing projected annual emissions with confidence interval."""

    point_estimate_kg = serializers.DecimalField(max_digits=12, decimal_places=3)
    lower_bound_kg = serializers.DecimalField(max_digits=12, decimal_places=3)
    upper_bound_kg = serializers.DecimalField(max_digits=12, decimal_places=3)
    period_days = serializers.IntegerField()
    confidence_pct = serializers.DecimalField(max_digits=5, decimal_places=2)
    point_estimate_tonnes = serializers.DecimalField(max_digits=12, decimal_places=3)
    lower_bound_tonnes = serializers.DecimalField(max_digits=12, decimal_places=3)
    upper_bound_tonnes = serializers.DecimalField(max_digits=12, decimal_places=3)


class FootprintResultSerializer(serializers.ModelSerializer):
    """Serializer representing saved FootprintEntry alongside breakdown and annual projection."""

    categories = CategoryBreakdownSerializer(many=True, read_only=True)
    annual_projection = serializers.SerializerMethodField()
    total_co2e_tonnes = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = FootprintEntry
        fields = [
            "id",
            "date",
            "mode",
            "total_co2e_kg",
            "total_co2e_tonnes",
            "factor_version",
            "period_days",
            "categories",
            "annual_projection",
            "created_at",
        ]
        read_only_fields = fields

    def get_annual_projection(self, obj: FootprintEntry) -> dict | None:
        """Compute the annual projection bounds dynamically."""
        from services.calculator_service import CalculatorService
        svc = CalculatorService()
        proj = svc._compute_annual_projection(obj.total_co2e_kg, obj.period_days)
        return AnnualProjectionSerializer(proj).data
