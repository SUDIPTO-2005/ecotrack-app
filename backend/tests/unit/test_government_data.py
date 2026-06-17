import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import httpx
from apps.data_sync.models import NationalAverageDataset
from services.government_data import GovernmentDataService

@pytest.fixture
def gov_service():
    return GovernmentDataService()

@patch("httpx.get")
def test_sync_owid_data_success(mock_get, db, gov_service):
    csv_url = "https://example.com/co2.csv"
    mock_csv = (
        "country,year,iso_code,co2_per_capita\n"
        "India,2022,IND,1.9\n"
        "United States,2022,USA,14.5\n"
        "Old Year,2010,IND,1.2\n"  # should be skipped because year < 2018
        "Future Year,2028,IND,2.1\n"  # should be skipped because year > 2026
        "Negative CO2,2022,GBR,-1.5\n"  # should be skipped because < 0
        "Invalid ISO,2022,XYZ,2.0\n"  # should be skipped because XYZ is not in map
        "Missing Data,2022,IND,\n"  # should be skipped because missing co2
    )
    
    mock_resp = MagicMock()
    mock_resp.text = mock_csv
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp
    
    result = gov_service.sync_owid_data(csv_url)
    assert result["synced"] == 2
    assert result["skipped"] == 5
    
    ind = NationalAverageDataset.objects.get(country_code="IN", year=2022)
    assert ind.per_capita_co2e_tonnes == Decimal("1.9")
    
    usa = NationalAverageDataset.objects.get(country_code="US", year=2022)
    assert usa.per_capita_co2e_tonnes == Decimal("14.5")

@patch("httpx.get")
def test_sync_owid_data_download_failure(mock_get, gov_service):
    csv_url = "https://example.com/co2.csv"
    mock_get.side_effect = httpx.HTTPError("404 Not Found")
    
    with pytest.raises(RuntimeError):
        gov_service.sync_owid_data(csv_url)
