"""
Schema validation and column ordering.

Loads config/schema.json and validates records against the 34-column standard.

Usage:
    from core.schema import validate_record, get_column_order
    errors = validate_record(record_dict)
    columns = get_column_order()
"""

import json
from pathlib import Path
from core.exceptions import SchemaValidationError


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "config" / "schema.json"

_schema_cache = None


def _load_schema() -> dict:
    """Load and cache the schema."""
    global _schema_cache
    if _schema_cache is None:
        with open(SCHEMA_PATH, "r") as f:
            _schema_cache = json.load(f)
    return _schema_cache


def get_column_order() -> list[str]:
    """Return the canonical 34-column order."""
    return _load_schema()["columns"]


def get_defaults() -> dict:
    """Return default values for optional fields."""
    return _load_schema().get("defaults", {})


def validate_record(record: dict) -> list[str]:
    """
    Validate a record dict against the schema.

    Args:
        record: Dict with field names as keys.

    Returns:
        List of validation error messages. Empty list = valid.
    """
    errors = []
    columns = get_column_order()

    # Required fields
    required = ["County", "Booking_Number", "Full_Name"]
    for field in required:
        if not record.get(field):
            errors.append(f"Missing required field: {field}")

    # Warn about unknown fields
    known = set(columns)
    for key in record:
        if key not in known:
            errors.append(f"Unknown field: {key}")

    return errors


def record_to_row(record: dict) -> list:
    """
    Convert a record dict to a list in canonical column order.
    Missing fields get empty string or default value.

    Args:
        record: Dict with field names as keys.

    Returns:
        List of values in the 34-column order.
    """
    columns = get_column_order()
    defaults = get_defaults()
    return [record.get(col, defaults.get(col, "")) for col in columns]
