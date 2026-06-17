"""
Emission factor data loader for EcoTrack.

Loads versioned emission factor datasets from JSON files and provides
a typed interface to the calculator service. Validates data integrity
on load so bad data fails fast, not silently.

Usage::

    from emission_factors.loader import get_factor, get_all_factors

    factor = get_factor("transport.car.petrol.average.per_km", version="2023-v1")
    print(factor.factor_value)  # Decimal("0.17003")
"""
from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent / "data"

# Map source_version prefixes to their data files.
# Factors from third-party studies (Scarborough, CEA, Apple, WRAP, IEA)
# are bundled inside the DEFRA 2023 file for convenience.
_VERSION_FILE_MAP: dict[str, str] = {
    "2023-v1": "defra_2023.json",
    "ipcc-ar6-2022": "ipcc_ar6.json",
    "scarborough-2023": "defra_2023.json",
    "cea-v18": "defra_2023.json",
    "apple-epd-2023": "defra_2023.json",
    "wrap-2017-defra-2023": "defra_2023.json",
    "iea-weo-2023": "defra_2023.json",
}

# Default version used when no version is specified by the caller.
DEFAULT_VERSION = "2023-v1"


@dataclass(frozen=True)
class FactorRecord:
    """Immutable emission factor record loaded from a data file.

    All numeric values are stored as :class:`decimal.Decimal` to avoid
    floating-point rounding errors during downstream calculations.
    """

    factor_id: str
    category: str
    subcategory: str
    factor_value: Decimal
    unit: str
    source: str
    source_url: str
    source_version: str
    effective_date: str
    notes: str = ""


@lru_cache(maxsize=4)
def _load_file(filename: str) -> list[dict]:
    """Load and parse a factor data file, caching the result in-process.

    The cache is keyed by filename, so each file is read from disk exactly
    once per interpreter lifetime.  Call ``_load_file.cache_clear()`` in
    tests that need a clean slate.

    Args:
        filename: Base filename within the ``data/`` directory.

    Returns:
        List of raw factor dicts from the JSON file.

    Raises:
        FileNotFoundError: If the data file does not exist on disk.
        ValueError: If the JSON is malformed or missing the ``factors`` key.
    """
    path = _DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Emission factor data file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)

    if "factors" not in data:
        raise ValueError(f"Data file '{filename}' is missing the top-level 'factors' key.")

    logger.info(
        "Loaded emission factor file",
        extra={
            "file": filename,
            "count": len(data["factors"]),
            "source_version": data.get("metadata", {}).get("version", "unknown"),
        },
    )
    return data["factors"]  # type: ignore[return-value]


def _parse_record(raw: dict) -> FactorRecord:
    """Parse a raw dict into a typed, validated :class:`FactorRecord`.

    Args:
        raw: Dict deserialized from a JSON data file entry.

    Returns:
        A validated, immutable :class:`FactorRecord`.

    Raises:
        ValueError: If any required field is absent from *raw*.
    """
    required_fields = [
        "factor_id",
        "category",
        "subcategory",
        "factor_value",
        "unit",
        "source",
        "source_url",
        "source_version",
        "effective_date",
    ]
    missing = [f for f in required_fields if f not in raw]
    if missing:
        raise ValueError(
            f"Emission factor record is missing required fields {missing!r}: {raw!r}"
        )

    return FactorRecord(
        factor_id=raw["factor_id"],
        category=raw["category"],
        subcategory=raw["subcategory"],
        factor_value=Decimal(str(raw["factor_value"])),
        unit=raw["unit"],
        source=raw["source"],
        source_url=raw["source_url"],
        source_version=raw["source_version"],
        effective_date=raw["effective_date"],
        notes=raw.get("notes", ""),
    )


def iter_all_factors(version: str = DEFAULT_VERSION) -> Iterator[FactorRecord]:
    """Iterate over every emission factor for a given source version.

    When *version* is not recognised the loader falls back to the DEFRA 2023
    dataset and logs a warning so callers are not silently served wrong data.

    Args:
        version: Source version string, e.g. ``'2023-v1'`` or ``'ipcc-ar6-2022'``.

    Yields:
        :class:`FactorRecord` instances, one per factor in the dataset.
    """
    filename = _VERSION_FILE_MAP.get(version)
    if filename is None:
        logger.warning(
            "Unknown emission factor version '%s', falling back to DEFRA 2023.",
            version,
        )
        filename = "defra_2023.json"

    for raw in _load_file(filename):
        yield _parse_record(raw)


def get_factor(factor_id: str, version: str = DEFAULT_VERSION) -> FactorRecord:
    """Return a single emission factor looked up by its stable dot-notation ID.

    Args:
        factor_id: Dot-notation factor ID, e.g.
            ``'transport.car.petrol.average.per_km'``.
        version: Source version string.  Defaults to :data:`DEFAULT_VERSION`.

    Returns:
        The matching :class:`FactorRecord`.

    Raises:
        KeyError: If no factor with *factor_id* exists in *version*.
    """
    for record in iter_all_factors(version):
        if record.factor_id == factor_id:
            return record

    raise KeyError(
        f"Emission factor '{factor_id}' not found in version '{version}'. "
        "Check emission_factors/data/ for available factor IDs."
    )


def get_factors_by_category(
    category: str,
    version: str = DEFAULT_VERSION,
) -> list[FactorRecord]:
    """Return all emission factors belonging to a given top-level category.

    Args:
        category: Category string, e.g. ``'transport'``, ``'energy'``,
            ``'diet'``, ``'consumption'``, or ``'waste'``.
        version: Source version string.

    Returns:
        List of matching :class:`FactorRecord` instances (may be empty).
    """
    return [
        record
        for record in iter_all_factors(version)
        if record.category == category
    ]


def get_current_version() -> str:
    """Return the default emission factor version string used by this loader.

    Returns:
        The :data:`DEFAULT_VERSION` constant, e.g. ``'2023-v1'``.
    """
    return DEFAULT_VERSION
