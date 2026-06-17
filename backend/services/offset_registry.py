"""
Offset Registry proxy service (Phase 8).

Fetches carbon offset projects from Patch.io sandbox registry or parses mock
fixtures if no API key is specified (informational only mode).
"""
from __future__ import annotations

import logging
from decimal import Decimal
from django.conf import settings
import httpx

from apps.offsets.models import OffsetProject

logger = logging.getLogger(__name__)


class OffsetRegistryService:
    """Service communicating with sandbox registries or returns local comparison baselines."""

    def sync_projects(self) -> dict[str, int]:
        """
        Fetch available offset projects from sandbox registry or load mock defaults.
        
        Returns:
            Dict containing stats of synced and skipped entries.
        """
        api_key = getattr(settings, "PATCH_API_KEY", "")
        mode = getattr(settings, "OFFSET_MARKETPLACE_MODE", "informational")

        logger.info("Syncing offset projects", extra={"mode": mode, "has_key": bool(api_key)})

        if not api_key:
            logger.info("Patch API key not set; loading mock offset projects.")
            return self._load_mock_projects()

        try:
            # Connect to Patch.io sandbox API proxy
            headers = {"Authorization": f"Bearer {api_key}"}
            response = httpx.get("https://api.patch.io/v1/projects", headers=headers, timeout=15.0)
            response.raise_for_status()
            
            data = response.json()
            synced_count = 0
            
            for proj in data.get("data", []):
                project_id = proj.get("id")
                name = proj.get("name")
                # Price is typically in cents/grams in Patch API, convert to USD/tonne
                price_cents = proj.get("average_price_per_tonne_cents_usd", 1500)
                price = Decimal(str(price_cents)) / Decimal("100")
                
                OffsetProject.objects.update_or_create(
                    project_id=project_id,
                    defaults={
                        "name": name,
                        "description": proj.get("description", ""),
                        "registry": "Patch.io",
                        "price_per_tonne_usd": price,
                        "certification": "VCS",
                        "project_url": "https://www.patch.io/",
                        "is_available": proj.get("status") == "active",
                    }
                )
                synced_count += 1
                
            return {"synced": synced_count}

        except Exception as exc:
            logger.error("Sandbox registry sync failed, falling back to mock defaults", exc_info=exc)
            return self._load_mock_projects()

    def _load_mock_projects(self) -> dict[str, int]:
        """Load fallback mock projects for user information."""
        mocks = [
            {
                "project_id": "proj_mock_reforestation_1",
                "name": "Western India Agro-Forestry Initiative",
                "description": "Reforestation and biodiversity protection projects across rural farm borders.",
                "registry": "Gold Standard",
                "price_per_tonne_usd": Decimal("18.50"),
                "certification": "GS-VER",
                "project_url": "https://www.goldstandard.org/",
            },
            {
                "project_id": "proj_mock_solar_2",
                "name": "Rajasthan Grid Solar Power Project",
                "description": "Accelerates grid transition to clean solar energy, replacing local coal baselines.",
                "registry": "Verra",
                "price_per_tonne_usd": Decimal("12.00"),
                "certification": "VCS",
                "project_url": "https://verra.org/",
            },
            {
                "project_id": "proj_mock_cookstoves_3",
                "name": "Improved Cookstoves for Rural Households",
                "description": "Distributes high-efficiency biomass stoves, cutting fuelwood demand and indoor pollution.",
                "registry": "Verra",
                "price_per_tonne_usd": Decimal("9.50"),
                "certification": "VCS-CCB",
                "project_url": "https://verra.org/",
            }
        ]

        synced_count = 0
        for mock in mocks:
            OffsetProject.objects.update_or_create(
                project_id=mock["project_id"],
                defaults={
                    "name": mock["name"],
                    "description": mock["description"],
                    "registry": mock["registry"],
                    "price_per_tonne_usd": mock["price_per_tonne_usd"],
                    "certification": mock["certification"],
                    "project_url": mock["project_url"],
                    "is_available": True,
                }
            )
            synced_count += 1

        return {"synced": synced_count}
