"""
Integration tests for the AI Coach API endpoints (Phase 7).
"""
from __future__ import annotations

import pytest
from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.calculator.models import FootprintEntry, FootprintCategory, CalculatorMode
from apps.ai_coach.models import AiCoachingSession


@pytest.fixture
def registered_user(db) -> User:
    return User.objects.create_user(
        username="coach.tester@ecotrack.example.com",
        email="coach.tester@ecotrack.example.com",
        password="GreenPlanet2024!",
    )


@pytest.fixture
def auth_client(registered_user) -> APIClient:
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(registered_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def user_footprint(db, registered_user) -> FootprintEntry:
    """Populate latest calculation record."""
    entry = FootprintEntry.objects.create(
        user=registered_user,
        date=date.today(),
        mode=CalculatorMode.QUICK,
        total_co2e_kg=3500.0,
        factor_version="2023-v1",
        raw_data={},
        period_days=365,
    )
    FootprintCategory.objects.create(
        entry=entry,
        category="transport",
        co2e_kg=2000.0,
        percentage=57.14,
    )
    FootprintCategory.objects.create(
        entry=entry,
        category="energy",
        co2e_kg=1500.0,
        percentage=42.86,
    )
    return entry


@pytest.mark.django_db
class TestAiCoachAPI:
    """Tests for retrieve weekly coaching tips endpoint."""

    def test_get_tips_success_fallback(self, auth_client, user_footprint):
        """POST /api/v1/ai-coach/tips/ returns fallback tips when API key is blank."""
        url = reverse("ai-coach-tips")
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["was_fallback"] is True
        assert data["model_version"] == "fallback"
        assert len(data["tips"]) > 0
        assert data["tips"][0]["category"] == "transport"

    def test_get_tips_checks_cache(self, auth_client, user_footprint, registered_user):
        """Second POST request within 7 days returns the cached session response."""
        url = reverse("ai-coach-tips")
        # Trigger first call
        res1 = auth_client.post(url)
        assert res1.status_code == status.HTTP_201_CREATED

        # Trigger second call
        res2 = auth_client.post(url)
        assert res2.status_code == status.HTTP_200_OK  # returns HTTP 200 OK from cache

        # Verify only 1 AiCoachingSession record exists
        assert AiCoachingSession.objects.filter(user=registered_user).count() == 1
