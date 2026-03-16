#!/usr/bin/env python3
"""
Universal County Runner — counties/{name}/runner.py

Generic pipeline orchestrator that works for ALL Python county scrapers:
  solver.scrape_{county}() → score → dedup → sheets (insert at row 2) → slack

This file is identical across counties. Only COUNTY_NAME changes.
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config_loader import load_config
from core.dedup import deduplicate
from core.logging_config import setup_logging
from core.writers.json_writer import write_json_output
from core.writers.slack_notifier import notify_slack


def run_pipeline(county_name: str, days_back: int = None, max_pages: int = None, dry_run: bool = False):
    """
    Run the full scraper pipeline for a county.

    1. Load config
    2. Import and run the county solver
    3. Deduplicate
    4. Score (if scorer available)
    5. Write to Google Sheets (insert at row 2 — newest first)
    6. Write JSON backup
    7. Notify Slack
    """
    config = load_config(county_name)
    logger = setup_logging(county_name)

    # Override config with CLI args
    if days_back is not None:
        config['scraper']['days_back'] = days_back
    if max_pages is not None:
        config['scraper']['max_pages'] = max_pages

    logger.info(f"Starting {county_name} scraper pipeline")
    logger.info(f"  days_back={config['scraper']['days_back']}, max_pages={config['scraper']['max_pages']}")

    # --- Step 1: Run the solver ---
    try:
        # Try importing the county's solve function dynamically
        solver_module = __import__(f"counties.{county_name}.solver", fromlist=['*'])

        # Look for scrape_{county_name} function
        scrape_fn_name = f"scrape_{county_name}"
        if hasattr(solver_module, scrape_fn_name):
            scrape_fn = getattr(solver_module, scrape_fn_name)
        elif hasattr(solver_module, 'scrape'):
            scrape_fn = solver_module.scrape
        elif hasattr(solver_module, 'main'):
            scrape_fn = solver_module.main
        else:
            logger.error(f"No scrape function found in counties.{county_name}.solver")
            return None

        # Call solver with appropriate args
        import inspect
        sig = inspect.signature(scrape_fn)
        kwargs = {}
        if 'days_back' in sig.parameters:
            kwargs['days_back'] = config['scraper']['days_back']
        if 'max_pages' in sig.parameters:
            kwargs['max_pages'] = config['scraper']['max_pages']

        records = scrape_fn(**kwargs)

        if records is None:
            records = []
        if isinstance(records, str):
            records = json.loads(records)

        logger.info(f"Solver returned {len(records)} records")

    except Exception as e:
        logger.error(f"Solver failed: {e}", exc_info=True)
        notify_slack(
            county=county_name,
            message=f"❌ {county_name} solver FAILED: {e}",
            level="error"
        )
        return None

    if not records:
        logger.warning("No records returned by solver")
        return {'total': 0, 'new': 0, 'dupes': 0}

    # --- Step 2: Deduplicate within batch ---
    unique_records = deduplicate(records)
    logger.info(f"After dedup: {len(unique_records)} unique (removed {len(records) - len(unique_records)} dupes)")

    # --- Step 3: Score records (if lead_scorer available) ---
    try:
        from python_scrapers.models.arrest_record import ArrestRecord
        from python_scrapers.scoring.lead_scorer import score_and_update

        for record in unique_records:
            try:
                ar = ArrestRecord.from_dict(record)
                scored = score_and_update(ar)
                record['Lead_Score'] = scored.Lead_Score
                record['Lead_Status'] = scored.Lead_Status
            except Exception:
                record.setdefault('Lead_Score', 0)
                record.setdefault('Lead_Status', 'Cold')
    except ImportError:
        logger.info("Lead scorer not available, skipping scoring")
        for record in unique_records:
            record.setdefault('Lead_Score', 0)
            record.setdefault('Lead_Status', 'Cold')

    # --- Step 4: Write to Google Sheets (row 2 = newest) ---
    stats = {'total': len(records), 'new': 0, 'dupes': 0, 'qualified': 0}

    if not dry_run:
        try:
            from core.writers.sheets_writer import SheetsWriter
            sheets_id = os.getenv('GOOGLE_SHEETS_ID')
            if sheets_id:
                writer = SheetsWriter(sheets_id)
                result = writer.write_records(unique_records, county=county_name)
                stats['new'] = result.get('new_records', 0)
                stats['dupes'] = result.get('duplicates_skipped', 0)
                stats['qualified'] = result.get('qualified_records', 0)
                logger.info(f"Sheets: {stats['new']} new, {stats['dupes']} dupes, {stats['qualified']} qualified")

                # Log ingestion
                writer.log_ingestion(county_name, result)
            else:
                logger.warning("GOOGLE_SHEETS_ID not set, skipping Sheets write")
        except Exception as e:
            logger.error(f"Sheets write failed: {e}", exc_info=True)
    else:
        logger.info("DRY RUN — skipping Sheets write")

    # --- Step 5: Write JSON backup ---
    write_json_output(county_name, unique_records, record_type='normalized')

    # --- Step 5b: Mirror to MongoDB Atlas (non-fatal) ---
    if not dry_run:
        try:
            from core.writers.mongo_writer import write_to_mongo
            mongo_uri = os.getenv('MONGODB_URI')
            if mongo_uri:
                mongo_stats = write_to_mongo(unique_records, county=county_name)
                stats['mongo_inserted'] = mongo_stats.get('inserted', 0)
                stats['mongo_updated']  = mongo_stats.get('updated', 0)
                stats['mongo_errors']   = mongo_stats.get('errors', 0)
                logger.info(
                    f"MongoDB: {stats['mongo_inserted']} inserted, "
                    f"{stats['mongo_updated']} updated, "
                    f"{stats['mongo_errors']} errors"
                )
            else:
                logger.info("MONGODB_URI not set — skipping MongoDB Atlas write")
        except Exception as e:
            logger.error(f"MongoDB write failed (non-fatal): {e}", exc_info=True)
    else:
        logger.info("DRY RUN — skipping MongoDB write")

    # --- Step 6: Slack notification ---
    if stats['new'] > 0:
        notify_slack(
            county=county_name,
            message=(
                f"✅ *{county_name}* scraper complete\n"
                f"  📊 {stats['new']} new | {stats['dupes']} dupes | {stats['qualified']} qualified"
            ),
            level="success"
        )

    logger.info(f"Pipeline complete: {stats}")
    return stats


def main():
    parser = argparse.ArgumentParser(description='County scraper runner')
    parser.add_argument('--county', type=str, help='County name (auto-detected from folder)')
    parser.add_argument('--days-back', type=int, help='Override days_back config')
    parser.add_argument('--max-pages', type=int, help='Override max_pages config')
    parser.add_argument('--dry-run', action='store_true', help='Skip Sheets write')
    args = parser.parse_args()

    # Auto-detect county from directory name
    county = args.county or Path(__file__).resolve().parent.name

    results = run_pipeline(county, args.days_back, args.max_pages, args.dry_run)
    if results is None:
        sys.exit(1)

    # Print summary JSON to stdout
    print(json.dumps(results))


if __name__ == "__main__":
    main()
