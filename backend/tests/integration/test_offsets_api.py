"""
Integration tests for the Offset Marketplace API endpoints (Phase 8).
"""
from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.offsets.models import OffsetProject
from services.offset_registry import OffsetRegistryService

_registry_svc = OffsetRegistryService()


@pytest.fixture
def registered_user(db) -> User:
    return User.objects.create_user(
        username="offset.tester@ecotrack.example.com",
        email="offset.tester@ecotrack.example.com",
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
def populated_projects(db) -> int:
    """Populate fallback mock offsets database records."""
    stats = _registry_svc._load_mock_projects()
    return stats["synced"]


@pytest.mark.django_db
class TestOffsetsAPI:
    """Tests for offsets list, detail, and disclaimer verification."""

    def test_offsets_list_success(self, auth_client, populated_projects):
        """GET /api/v1/offsets/ returns list of offset projects and the compliance disclaimer."""
        url = reverse("offsets-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "disclaimer" in data
        assert "estimated offset costs for informational purposes only" in data["disclaimer"]
        assert len(data["results"]) == 3
        assert data["results"][0]["name"] == "Improved Cookstoves for Rural Households"

    def test_offsets_detail_success(self, auth_client, populated_projects):
        """GET /api/v1/offsets/<id>/ returns project details and the disclaimer."""
        proj = OffsetProject.objects.first()
        url = reverse("offsets-detail", kwargs={"pk": proj.pk})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "disclaimer" in data
        assert data["project"]["name"] == proj.name
