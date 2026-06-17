"""
Integration tests for the Calculator and Dashboard API endpoints (Phase 3).
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.calculator.models import FootprintEntry, FootprintCategory, CalculatorMode


@pytest.fixture
def registered_user(db) -> User:
    """Create a user for testing."""
    return User.objects.create_user(
        username="calculator.tester@ecotrack.example.com",
        email="calculator.tester@ecotrack.example.com",
        password="GreenPlanet2024!",
        country="IN",
    )


@pytest.fixture
def auth_client(registered_user) -> APIClient:
    """Return an authenticated client."""
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(registered_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.mark.django_db
class TestCalculatorAPI:
    """Tests for Quick and Detailed Calculator endpoints."""

    def test_quick_estimate_success(self, auth_client, registered_user):
        """POST /api/v1/calculator/estimate/ calculates and persists quick estimate."""
        payload = {
            "car_km_per_week": 150,
            "car_fuel_type": "petrol",
            "electricity_kwh_per_month": 250,
            "diet_type": "vegetarian",
            "flights_short_haul_per_year": 1,
            "flights_long_haul_per_year": 0,
            "period_days": 365,
        }
        url = reverse("calculator-estimate")
        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "total_co2e_kg" in data
        assert float(data["total_co2e_kg"]) > 0
        assert data["mode"] == "quick"
        assert len(data["categories"]) > 0

        # Check DB persistence
        entry = FootprintEntry.objects.filter(user=registered_user).first()
        assert entry is not None
        assert entry.mode == CalculatorMode.QUICK
        assert FootprintCategory.objects.filter(entry=entry).count() > 0

        # User onboarding should now be complete
        registered_user.refresh_from_db()
        assert registered_user.onboarding_complete is True

    def test_detailed_estimate_success(self, auth_client, registered_user):
        """POST /api/v1/calculator/detailed/ calculates and persists detailed estimate."""
        payload = {
            "car_km_per_week": 100,
            "car_fuel_type": "electric",
            "bus_km_per_week": 50,
            "rail_km_per_week": 200,
            "flights_short_haul_per_year": 2,
            "electricity_kwh_per_month": 120,
            "natural_gas_kwh_per_month": 80,
            "diet_type": "vegan",
            "new_clothing_items_per_year": 5,
            "waste_kg_per_week": 10,
            "recycling_fraction": 0.5,
            "period_days": 180,
        }
        url = reverse("calculator-detailed")
        response = auth_client.post(url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert float(data["total_co2e_kg"]) > 0
        assert data["mode"] == "detailed"

        # Check DB persistence
        entry = FootprintEntry.objects.filter(user=registered_user).first()
        assert entry is not None
        assert entry.mode == CalculatorMode.DETAILED
        assert entry.period_days == 180


@pytest.mark.django_db
class TestDashboardAPI:
    """Tests for Dashboard history, trends, compare, and projection endpoints."""

    @pytest.fixture
    def populated_data(self, registered_user):
        """Populate footprint entry history for the user."""
        entry = FootprintEntry.objects.create(
            user=registered_user,
            date=date.today() - timedelta(days=10),
            mode=CalculatorMode.QUICK,
            total_co2e_kg=Decimal("4500.000"),
            factor_version="2023-v1",
            raw_data={},
            period_days=365,
        )
        FootprintCategory.objects.create(entry=entry, category="transport", co2e_kg=Decimal("2000.0"), percentage=Decimal("44.4"))
        FootprintCategory.objects.create(entry=entry, category="energy", co2e_kg=Decimal("1500.0"), percentage=Decimal("33.3"))
        return entry

    def test_dashboard_history(self, auth_client, populated_data):
        """GET /api/v1/dashboard/history/ returns footprint history list."""
        url = reverse("dashboard-history")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == populated_data.id

    def test_dashboard_trends(self, auth_client, populated_data):
        """GET /api/v1/dashboard/trends/ returns overall breakdown and time-series lists."""
        url = reverse("dashboard-trends")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "time_series" in data
        assert "overall_category_breakdown_kg" in data
        assert float(data["overall_category_breakdown_kg"]["transport"]) == 2000.0

    def test_dashboard_compare(self, auth_client, populated_data):
        """GET /api/v1/dashboard/compare/ returns user vs average per-capita tonnes comparison."""
        url = reverse("dashboard-compare")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user_annualised_tonnes" in data
        assert "national_average_tonnes" in data
        assert data["country_code"] == "IN"

    def test_dashboard_projection(self, auth_client, populated_data):
        """GET /api/v1/dashboard/projection/ returns projected bounds and interval width."""
        url = reverse("dashboard-projection")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "projection" in data
        assert float(data["projection"]["point_estimate_kg"]) == 4500.0
