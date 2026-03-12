"""
Deduplication — checks for existing records by Booking_Number + County.

Usage:
    from core.dedup import deduplicate
    unique_records = deduplicate(records, "charlotte")
"""

import sys


def get_dedup_key(record: dict) -> str:
    """Generate a dedup key from a record."""
    booking = record.get("Booking_Number", "").strip()
    county = record.get("County", "").strip()
    return f"{county}|{booking}" if booking else ""


def deduplicate(records: list[dict], county_name: str = "") -> list[dict]:
    """
    Remove duplicate records from a list.
    Dedup key is Booking_Number + County.

    Args:
        records: List of normalized record dicts
        county_name: County name for logging

    Returns:
        De-duplicated list (preserves first occurrence)
    """
    seen = set()
    unique = []
    duplicates = 0

    for record in records:
        key = get_dedup_key(record)
        if not key:
            unique.append(record)  # No dedup key = keep it
            continue
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(record)

    if duplicates > 0:
        sys.stderr.write(
            f"🔍 [{county_name}] Dedup: {len(records)} → {len(unique)} "
            f"({duplicates} duplicates removed)\n"
        )

    return unique
