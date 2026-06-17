"""
Views for the calculator app (Phase 3).

Exposes POST endpoints to evaluate and persist quick or detailed
carbon footprint estimates for users.
"""
from __future__ import annotations

from datetime import date

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.calculator_service import (
    CalculatorService,
    DetailedCalculatorInput,
    QuickCalculatorInput,
)

from .models import CalculatorMode, FootprintCategory, FootprintEntry
from .serializers import (
    DetailedCalculatorInputSerializer,
    FootprintResultSerializer,
    QuickCalculatorInputSerializer,
)

_calculator_service = CalculatorService()


class QuickEstimateView(APIView):
    """POST /api/v1/calculator/estimate/ — Quick mode footprint calculation.

    Takes 5 inputs and returns calculated CO2e values, saving a FootprintEntry
    and FootprintCategory breakdown records for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """Run quick mode calculation."""
        serializer = QuickCalculatorInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        calc_input = QuickCalculatorInput(
            car_km_per_week=data["car_km_per_week"],
            car_fuel_type=data["car_fuel_type"],
            electricity_kwh_per_month=data["electricity_kwh_per_month"],
            diet_type=data["diet_type"],
            flights_short_haul_per_year=data["flights_short_haul_per_year"],
            flights_long_haul_per_year=data["flights_long_haul_per_year"],
            country_grid_version=data["country_grid_version"],
            electricity_factor_id=data["electricity_factor_id"],
            period_days=data["period_days"],
        )

        result = _calculator_service.calculate_quick(calc_input)
        entry_date = data.get("date") or date.today()

        # Save to database
        entry = FootprintEntry.objects.create(
            user=request.user,
            date=entry_date,
            mode=CalculatorMode.QUICK,
            total_co2e_kg=result.total_co2e_kg,
            factor_version=result.factor_version,
            raw_data=request.data,
            period_days=result.period_days,
        )

        for cat in result.categories:
            FootprintCategory.objects.create(
                entry=entry,
                category=cat.category,
                co2e_kg=cat.co2e_kg,
                percentage=cat.percentage,
                sub_breakdown=cat.sub_breakdown,
            )

        # Mark onboarding complete
        if not request.user.onboarding_complete:
            request.user.onboarding_complete = True
            request.user.save(update_fields=["onboarding_complete"])

        return Response(
            FootprintResultSerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )


class DetailedEstimateView(APIView):
    """POST /api/v1/calculator/detailed/ — Detailed mode calculation.

    Takes 20+ inputs and returns calculated CO2e values, saving a FootprintEntry
    and FootprintCategory breakdown records for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        """Run detailed mode calculation."""
        serializer = DetailedCalculatorInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        calc_input = DetailedCalculatorInput(
            car_km_per_week=data["car_km_per_week"],
            car_fuel_type=data["car_fuel_type"],
            bus_km_per_week=data["bus_km_per_week"],
            rail_km_per_week=data["rail_km_per_week"],
            motorbike_km_per_week=data["motorbike_km_per_week"],
            flights_short_haul_per_year=data["flights_short_haul_per_year"],
            flights_long_haul_per_year=data["flights_long_haul_per_year"],
            electricity_kwh_per_month=data["electricity_kwh_per_month"],
            electricity_factor_id=data["electricity_factor_id"],
            natural_gas_kwh_per_month=data["natural_gas_kwh_per_month"],
            heating_oil_litres_per_year=data["heating_oil_litres_per_year"],
            diet_type=data["diet_type"],
            new_clothing_items_per_year=data["new_clothing_items_per_year"],
            new_electronics_laptops_per_year=data["new_electronics_laptops_per_year"],
            new_electronics_smartphones_per_year=data["new_electronics_smartphones_per_year"],
            waste_kg_per_week=data["waste_kg_per_week"],
            recycling_fraction=data["recycling_fraction"],
            food_waste_kg_per_week=data["food_waste_kg_per_week"],
            factor_version=data["factor_version"],
            period_days=data["period_days"],
        )

        result = _calculator_service.calculate_detailed(calc_input)
        entry_date = data.get("date") or date.today()

        # Save to database
        entry = FootprintEntry.objects.create(
            user=request.user,
            date=entry_date,
            mode=CalculatorMode.DETAILED,
            total_co2e_kg=result.total_co2e_kg,
            factor_version=result.factor_version,
            raw_data=request.data,
            period_days=result.period_days,
        )

        for cat in result.categories:
            FootprintCategory.objects.create(
                entry=entry,
                category=cat.category,
                co2e_kg=cat.co2e_kg,
                percentage=cat.percentage,
                sub_breakdown=cat.sub_breakdown,
            )

        # Mark onboarding complete
        if not request.user.onboarding_complete:
            request.user.onboarding_complete = True
            request.user.save(update_fields=["onboarding_complete"])

        return Response(
            FootprintResultSerializer(entry).data,
            status=status.HTTP_201_CREATED,
        )
