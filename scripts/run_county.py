#!/usr/bin/env python3
"""
CLI — Run a single county scraper.

Usage:
    python scripts/run_county.py charlotte
    python scripts/run_county.py charlotte --days-back 7 --dry-run
    python scripts/run_county.py charlotte --max-pages 5
"""

import sys
import argparse
import importlib
from pathlib import Path

# Ensure repo root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config_loader import load_config, get_active_counties


def main():
    parser = argparse.ArgumentParser(
        description="Run a county arrest scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Active counties: {', '.join(get_active_counties())}"
    )
    parser.add_argument("county", help="County name (e.g., charlotte, palm_beach)")
    parser.add_argument("--days-back", type=int, default=None)
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true", help="Don't write to Sheets")
    parser.add_argument("--no-slack", action="store_true", help="Skip Slack notifications")
    args = parser.parse_args()

    county = args.county.lower().replace(" ", "_").replace("-", "_")

    # Load config
    try:
        config = load_config(county)
    except Exception as e:
        sys.stderr.write(f"❌ Config error: {e}\n")
        sys.exit(1)

    # Override from CLI args
    if args.days_back:
        config["days_back"] = args.days_back
    if args.max_pages:
        config["max_pages"] = args.max_pages

    # Import and run the county runner
    try:
        runner_module = importlib.import_module(f"counties.{county}.runner")
    except ModuleNotFoundError:
        sys.stderr.write(
            f"❌ No runner found for '{county}'\n"
            f"   Expected: counties/{county}/runner.py\n"
            f"   Copy from: counties/_template/runner.py\n"
        )
        sys.exit(1)

    stats = runner_module.run(county, config, dry_run=args.dry_run)

    # Exit with non-zero if there were errors
    if stats.get("errors"):
        sys.exit(1)


if __name__ == "__main__":
    main()
