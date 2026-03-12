"""
Normalizer — maps raw scraper output to the 34-column schema.

Handles field alias resolution, date normalization, bond amount parsing, etc.

Usage:
    from core.normalizer import normalize_record, normalize_records
    normalized = normalize_records(raw_records, "charlotte")
"""

import json
import re
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ALIASES_PATH = REPO_ROOT / "config" / "field_aliases.json"

_aliases_cache = None


def _load_aliases() -> dict:
    """Load and cache field aliases."""
    global _aliases_cache
    if _aliases_cache is None:
        with open(ALIASES_PATH, "r") as f:
            _aliases_cache = json.load(f)
    return _aliases_cache


def _resolve_field(raw_key: str, aliases: dict) -> str:
    """
    Resolve a raw field name to its canonical schema name using aliases.

    Args:
        raw_key: The raw field name from a scraper
        aliases: The alias mapping dict

    Returns:
        Canonical field name, or the original key if no alias matches
    """
    raw_lower = raw_key.lower().strip()
    for canonical, alias_list in aliases.items():
        if raw_lower in [a.lower() for a in alias_list]:
            return canonical
    return raw_key


def normalize_bond_amount(value) -> str:
    """Parse a bond amount string into a clean numeric string."""
    if not value:
        return "0"
    if isinstance(value, (int, float)):
        return str(value)
    # Remove $ , and whitespace
    cleaned = re.sub(r'[,$\s]', '', str(value))
    try:
        return str(float(cleaned))
    except ValueError:
        return "0"


def normalize_date(value: str) -> str:
    """
    Normalize date strings to YYYY-MM-DD format.
    Handles: MM/DD/YYYY, YYYY-MM-DD, M/D/YYYY, etc.
    """
    if not value:
        return ""
    value = value.strip().split()[0]  # Take just the date part if datetime

    formats = [
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
        "%d-%b-%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value  # Return as-is if no format matched


def normalize_record(raw: dict, county_name: str) -> dict:
    """
    Normalize a single raw record dict to the canonical schema.

    Args:
        raw: Raw record dict from a county solver
        county_name: County name for the County field

    Returns:
        Normalized record dict with canonical field names
    """
    aliases = _load_aliases()
    normalized = {}

    # Map raw keys to canonical names
    for raw_key, value in raw.items():
        canonical = _resolve_field(raw_key, aliases)
        if canonical not in normalized or not normalized[canonical]:
            normalized[canonical] = value

    # Ensure required fields
    normalized["County"] = county_name.replace("_", " ").title()
    normalized["State"] = normalized.get("State", "FL")

    # Add scrape timestamp if missing
    if "Scrape_Timestamp" not in normalized:
        normalized["Scrape_Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Normalize specific fields
    if "Bond_Amount" in normalized:
        normalized["Bond_Amount"] = normalize_bond_amount(normalized["Bond_Amount"])
    if "Booking_Date" in normalized:
        normalized["Booking_Date"] = normalize_date(normalized["Booking_Date"])
    if "DOB" in normalized:
        normalized["DOB"] = normalize_date(normalized["DOB"])

    return normalized


def normalize_records(raw_records: list[dict], county_name: str) -> list[dict]:
    """Normalize a list of raw records."""
    return [normalize_record(r, county_name) for r in raw_records]
