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


def write_json_output(*args, **kwargs):
    """
    Wrapper that handles both calling conventions:
      - write_json_output(records, county_name, stage='raw')        ← correct
      - write_json_output(county_name, records, record_type='...')  ← runner.py convention
    """
    # Map record_type → stage if used
    if 'record_type' in kwargs:
        kwargs['stage'] = kwargs.pop('record_type')

    if len(args) >= 2:
        # Detect swapped args: if first arg is a string, it's the county name
        if isinstance(args[0], str) and isinstance(args[1], list):
            # Swapped: (county_name, records, ...) → fix to (records, county_name, ...)
            args = (args[1], args[0]) + args[2:]

    return write_json(*args, **kwargs)
