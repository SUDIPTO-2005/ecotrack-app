import pytest
from decimal import Decimal
from django.conf import settings
from unittest.mock import patch, MagicMock
import httpx
from apps.offsets.models import OffsetProject
from services.offset_registry import OffsetRegistryService

@pytest.fixture
def offset_service():
    return OffsetRegistryService()

def test_sync_projects_no_api_key(db, offset_service, monkeypatch):
    monkeypatch.setattr(settings, "PATCH_API_KEY", "")
    monkeypatch.setattr(settings, "OFFSET_MARKETPLACE_MODE", "informational")
    
    # Check that it loads the mock projects
    result = offset_service.sync_projects()
    assert result["synced"] == 3
    assert OffsetProject.objects.filter(project_id="proj_mock_reforestation_1").exists()

@patch("httpx.get")
def test_sync_projects_with_api_key_success(mock_get, db, offset_service, monkeypatch):
    monkeypatch.setattr(settings, "PATCH_API_KEY", "test-patch-key")
    
    mock_response = {
        "data": [
            {
                "id": "proj_patch_1",
                "name": "Patch Forestry Project",
                "description": "A sandbox test forestry project.",
                "average_price_per_tonne_cents_usd": 2500,
                "status": "active"
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.json = MagicMock(return_value=mock_response)
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp
    
    result = offset_service.sync_projects()
    assert result["synced"] == 1
    
    proj = OffsetProject.objects.get(project_id="proj_patch_1")
    assert proj.name == "Patch Forestry Project"
    assert proj.price_per_tonne_usd == Decimal("25.00")
    assert proj.is_available is True

@patch("httpx.get")
def test_sync_projects_api_failure_fallback(mock_get, db, offset_service, monkeypatch):
    monkeypatch.setattr(settings, "PATCH_API_KEY", "test-patch-key")
    mock_get.side_effect = httpx.HTTPError("500 Server Error")
    
    # Should fallback to mock defaults
    result = offset_service.sync_projects()
    assert result["synced"] == 3
    assert OffsetProject.objects.filter(project_id="proj_mock_solar_2").exists()
