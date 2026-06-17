"""
Integration tests for the Challenges and Leaderboard API endpoints (Phase 5).
"""
from __future__ import annotations

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.challenges.models import Challenge, ChallengeParticipant, Badge, UserBadge, LeaderboardSnapshot


@pytest.fixture
def registered_user(db) -> User:
    return User.objects.create_user(
        username="challenges.tester@ecotrack.example.com",
        email="challenges.tester@ecotrack.example.com",
        password="GreenPlanet2024!",
        country="IN",
        city="Mumbai",
        display_name="challenges.tester@ecotrack.example.com",
        privacy_level="public",
        leaderboard_visible=True,
    )


@pytest.fixture
def auth_client(registered_user) -> APIClient:
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(registered_user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


@pytest.fixture
def sample_challenge(db) -> Challenge:
    return Challenge.objects.create(
        title="Zero Waste Week",
        description="Try to keep your waste output below 2kg.",
        category="waste",
        start_date=date.today() - timedelta(days=2),
        end_date=date.today() + timedelta(days=5),
        target_reduction_pct=15,
    )


@pytest.mark.django_db
class TestChallengesAPI:
    """Tests for Challenge list, join, and leave endpoints."""

    def test_challenges_list_success(self, auth_client, sample_challenge):
        """GET /api/v1/challenges/ returns active challenges."""
        url = reverse("challenges-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Zero Waste Week"
        assert data[0]["is_joined"] is False

    def test_challenge_join_success(self, auth_client, registered_user, sample_challenge):
        """POST /api/v1/challenges/<id>/join/ register user as participant."""
        url = reverse("challenges-join", kwargs={"pk": sample_challenge.pk})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_201_CREATED
        assert ChallengeParticipant.objects.filter(
            user=registered_user,
            challenge=sample_challenge,
        ).exists()

    def test_challenge_leave_success(self, auth_client, registered_user, sample_challenge):
        """POST /api/v1/challenges/<id>/leave/ unregisters user as participant."""
        ChallengeParticipant.objects.create(user=registered_user, challenge=sample_challenge)
        
        url = reverse("challenges-leave", kwargs={"pk": sample_challenge.pk})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not ChallengeParticipant.objects.filter(
            user=registered_user,
            challenge=sample_challenge,
        ).exists()


@pytest.mark.django_db
class TestLeaderboardAPI:
    """Tests for Leaderboard retrieve endpoint."""

    def test_leaderboard_global_success(self, auth_client, registered_user):
        """GET /api/v1/challenges/leaderboard/ returns ranking snapshots."""
        # Setup snapshot
        LeaderboardSnapshot.objects.create(
            user=registered_user,
            rank=1,
            reduction_percentage=Decimal("24.50"),
            scope="global",
        )

        url = reverse("leaderboard")
        response = auth_client.get(url, {"scope": "global"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["rank"] == 1
        assert data[0]["display_name"] == "challenges.tester@ecotrack.example.com"

    def test_leaderboard_requires_opt_in(self, auth_client, registered_user):
        """Leaderboard access returns 403 if user.leaderboard_visible is False."""
        registered_user.leaderboard_visible = False
        registered_user.save()

        url = reverse("leaderboard")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
