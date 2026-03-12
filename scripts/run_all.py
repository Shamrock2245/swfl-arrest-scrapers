#!/usr/bin/env python3
"""
CLI — Run all active county scrapers sequentially.

Usage:
    python scripts/run_all.py
    python scripts/run_all.py --dry-run
    python scripts/run_all.py --only charlotte,collier
"""

import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config_loader import load_config, get_active_counties
from core.logging_config import get_logger


def main():
    parser = argparse.ArgumentParser(description="Run all active county scrapers")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--only", type=str, help="Comma-separated list of counties")
    args = parser.parse_args()

    logger = get_logger("system")

    if args.only:
        counties = [c.strip().lower() for c in args.only.split(",")]
    else:
        counties = get_active_counties()

    logger.info(f"Running {len(counties)} counties: {counties}")
    results = {}

    for county in counties:
        try:
            import importlib
            runner = importlib.import_module(f"counties.{county}.runner")
            config = load_config(county)
            stats = runner.run(county, config, dry_run=args.dry_run)
            results[county] = stats
        except Exception as e:
            logger.error(f"{county}: {e}")
            results[county] = {"error": str(e)}

    # Summary
    print(f"\n{'='*60}")
    print("SCRAPER RUN SUMMARY")
    print(f"{'='*60}")
    for county, stats in results.items():
        status = "❌" if stats.get("error") or stats.get("errors") else "✅"
        new = stats.get("new_records", "?")
        print(f"  {status} {county.title()}: {new} new records")


if __name__ == "__main__":
    main()
