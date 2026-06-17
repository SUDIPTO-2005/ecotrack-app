"""
Integration tests for the Government Data Sync API endpoints (Phase 4).
"""
from __future__ import annotations

import pytest
import responses
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.data_sync.models import NationalAverageDataset


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.mark.django_db
class TestDataSyncAPI:
    """Tests for GovDataSyncWebhookView."""

    MOCK_CSV = (
        "country,year,co2,co2_per_capita,iso_code\n"
        "India,2021,2700.0,1.89,IND\n"
        "United States,2021,5000.0,14.85,USA\n"
        "World,2021,37000.0,4.45,OWID_WRL\n"
    )

    def test_sync_webhook_success(self, api_client, settings):
        """POST /api/v1/internal/sync/national-averages/ parses and upserts database."""
        settings.DATA_SYNC_SECRET = "test-secret"
        url = reverse("data-sync-national-averages")

        from unittest.mock import patch, MagicMock
        mock_response = MagicMock()
        mock_response.text = self.MOCK_CSV
        mock_response.status_code = 200

        with patch("httpx.get", return_value=mock_response) as mock_get:
            response = api_client.post(
                url,
                data={"csv_url": "http://mock-owid.example.com/co2-data.csv"},
                HTTP_X_SYNC_SECRET="test-secret",
                format="json",
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["synced"] == 3
            mock_get.assert_called_once_with("http://mock-owid.example.com/co2-data.csv", timeout=30.0)

        # Check DB updates
        ind = NationalAverageDataset.objects.get(country_code="IN", year=2021)
        assert float(ind.per_capita_co2e_tonnes) == 1.89
        
        world = NationalAverageDataset.objects.get(country_code="WRL", year=2021)
        assert float(world.per_capita_co2e_tonnes) == 4.45

    def test_sync_webhook_forbidden(self, api_client, settings):
        """Webhook fails with 403 status code when secret is invalid."""
        settings.DATA_SYNC_SECRET = "test-secret"
        url = reverse("data-sync-national-averages")

        response = api_client.post(
            url,
            data={},
            HTTP_X_SYNC_SECRET="wrong-secret",
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
