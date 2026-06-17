"""
Government data sync service (Phase 4).

Downloads CO2 per-capita datasets (e.g. Our World in Data) and updates
the local comparison baseline stats.
"""
from __future__ import annotations

import csv
import logging
from decimal import Decimal

import httpx

from apps.data_sync.models import NationalAverageDataset

logger = logging.getLogger(__name__)


class GovernmentDataService:
    """Service to handle fetching and parsing carbon averages from OWID."""

    # mapping of common 3-letter ISO codes (OWID standard) to 2-letter codes
    _ISO3_TO_ISO2 = {
        "IND": "IN", "USA": "US", "GBR": "GB", "DEU": "DE", "FRA": "FR",
        "CAN": "CA", "AUS": "AU", "JPN": "JP", "CHN": "CN", "BRA": "BR",
        "RUS": "RU", "ZAF": "ZA", "OWID_WRL": "WRL"  # Custom code for World average
    }

    def sync_owid_data(self, csv_url: str) -> dict[str, int]:
        """
        Download Our World in Data CO2 dataset in CSV format and upsert local database entries.

        Args:
            csv_url: Public url pointing to the CSV file.

        Returns:
            Dict containing stats of synced and skipped entries.
        """
        logger.info("Starting OWID data sync", extra={"csv_url": csv_url})

        try:
            response = httpx.get(csv_url, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to download OWID data", exc_info=exc)
            raise RuntimeError(f"OWID sync download failed: {exc}") from exc

        content = response.text
        lines = content.splitlines()
        reader = csv.DictReader(lines)

        synced_count = 0
        skipped_count = 0

        # We look for per-capita emissions. Column name in OWID CO2 dataset is typically 'co2_per_capita'
        # The CSV has headers: country, year, co2, co2_per_capita, etc.
        for row in reader:
            iso_code = row.get("iso_code")
            year_str = row.get("year")
            co2_per_capita_str = row.get("co2_per_capita") or row.get("co2_per_capita_e")

            if not iso_code or not year_str or not co2_per_capita_str:
                skipped_count += 1
                continue

            # Map three-letter code to two-letter country code
            iso2 = self._ISO3_TO_ISO2.get(iso_code)
            if not iso2:
                skipped_count += 1
                continue

            try:
                year = int(year_str)
                # Restrict to relatively recent and valid years to prevent huge DB bloat
                if year < 2018 or year > 2026:
                    skipped_count += 1
                    continue

                per_capita = Decimal(co2_per_capita_str)
                if per_capita < 0:
                    skipped_count += 1
                    continue

                # Upsert record
                NationalAverageDataset.objects.update_or_create(
                    country_code=iso2,
                    year=year,
                    defaults={
                        "per_capita_co2e_tonnes": per_capita,
                        "source": "Our World in Data (OWID) CO2 dataset",
                    }
                )
                synced_count += 1
            except (ValueError, ArithmeticError):
                skipped_count += 1
                continue

        logger.info("OWID data sync complete", extra={"synced": synced_count, "skipped": skipped_count})
        return {"synced": synced_count, "skipped": skipped_count}
