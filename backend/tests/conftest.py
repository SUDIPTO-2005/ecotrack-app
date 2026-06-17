"""
Pytest configuration and shared fixtures for EcoTrack backend tests.

These fixtures are available to all tests in the test suite.
External API calls (Anthropic, Patch.io, OWID) are NEVER made in tests —
all external clients must be mocked at this level.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Database fixtures (used in integration tests, Phase 3+)
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    """DRF APIClient for endpoint integration tests.

    Imported lazily so unit tests (which don't need Django) don't trigger
    Django setup unnecessarily.
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def user_factory(db):
    """Factory for creating test users with a known password."""
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def _create_user(email: str = "test@ecotrack.example.com", password: str = "TestPass123!"):
        return User.objects.create_user(
            username=email.split("@")[0],
            email=email,
            password=password,
        )

    return _create_user


@pytest.fixture
def authenticated_client(api_client, user_factory, db):
    """APIClient with a pre-authenticated user via JWT."""
    from rest_framework_simplejwt.tokens import RefreshToken

    user = user_factory()
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return api_client, user
