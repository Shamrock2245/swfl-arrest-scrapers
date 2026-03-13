"""
JSON file writer — writes raw, normalized, and failed records to output/.

Usage:
    from core.writers.json_writer import write_json
    write_json(records, "charlotte", stage="raw")
"""

import json
from pathlib import Path
from datetime import datetime


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def write_json(records: list[dict], county_name: str, stage: str = "raw",
               output_base: str = None) -> Path:
    """
    Write records to a JSON file in the output directory.

    Args:
        records: List of record dicts
        county_name: County name (used for folder)
        stage: One of "raw", "normalized", "failed"
        output_base: Override output base dir (default: output/)

    Returns:
        Path to the written file
    """
    if output_base:
        base = Path(output_base)
    else:
        base = REPO_ROOT / "output"

    output_dir = base / stage / county_name
    output_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}_{stage}.json"
    filepath = output_dir / filename

    with open(filepath, "w") as f:
        json.dump(records, f, indent=2, default=str)

    return filepath


# Alias for backward compatibility — county runners import this name
write_json_output = write_json
