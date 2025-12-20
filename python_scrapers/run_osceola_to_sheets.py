#!/usr/bin/env python3
"""
Osceola County Scraper Runner with Google Sheets Integration

Runs the Osceola County scraper and writes results to Google Sheets.

Usage:
    python3 run_osceola_to_sheets.py [--start MM/DD/YYYY] [--end MM/DD/YYYY]
    
Example:
    python3 run_osceola_to_sheets.py --start 12/10/2025 --end 12/20/2025
"""

import subprocess
import json
import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_scrapers.writers.simple_sheets_writer import write_to_sheets


def run_osceola_scraper(start_date, end_date=None):
    """Run the Osceola County scraper and return parsed records."""
    print("🏛️ Running Osceola County Scraper...")
    print(f"   Start date: {start_date}")
    print(f"   End date: {end_date or 'today'}")
    
    solver_path = os.path.join(
        os.path.dirname(__file__),
        'scrapers',
        'osceola_solver.py'
    )
    
    cmd = ['python3', solver_path, '--start', start_date]
    if end_date:
        cmd.extend(['--end', end_date])
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes timeout for multiple days
        )
        
        # Print stderr (progress logs)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode != 0:
            print(f"❌ Scraper failed with exit code {result.returncode}")
            return []
        
        raw_json = result.stdout.strip()
        if not raw_json:
            print("⚠️ No data returned from scraper")
            return []
        
        # Parse JSON
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # Try to find JSON array in output
            start = raw_json.find('[')
            end = raw_json.rfind(']') + 1
            if start != -1 and end > start:
                data = json.loads(raw_json[start:end])
            else:
                print("❌ Could not parse JSON output")
                return []
        
        print(f"✅ Scraped {len(data)} records")
        return data
        
    except subprocess.TimeoutExpired:
        print("❌ Scraper timed out")
        return []
    except Exception as e:
        print(f"❌ Error running scraper: {e}")
        return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Osceola County Scraper -> Google Sheets')
    parser.add_argument('--start', default='12/10/2025', help='Start date (MM/DD/YYYY)')
    parser.add_argument('--end', default=None, help='End date (MM/DD/YYYY), defaults to today')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Osceola County Scraper -> Google Sheets")
    print("=" * 60)
    
    # Run scraper
    records = run_osceola_scraper(args.start, args.end)
    
    if not records:
        print("No records to write")
        return
    
    # Write to Google Sheets
    print(f"\n📊 Writing {len(records)} records to Google Sheets...")
    stats = write_to_sheets(records, 'Osceola')
    
    print(f"\n📈 Results:")
    print(f"   Total records: {stats['total']}")
    print(f"   New records written: {stats['new']}")
    print(f"   Duplicates skipped: {stats['skipped']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
