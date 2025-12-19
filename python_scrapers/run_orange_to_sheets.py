#!/usr/bin/env python3
"""
Orange County Scraper Runner with Google Sheets Integration

Runs the Orange County PDF scraper and writes results to Google Sheets.

Usage:
    python3 run_orange_to_sheets.py
"""

import subprocess
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_scrapers.writers.simple_sheets_writer import write_to_sheets


def run_orange_scraper():
    """Run the Orange County scraper and return parsed records."""
    print("🔵 Running Orange County Scraper...")
    
    solver_path = os.path.join(
        os.path.dirname(__file__),
        'scrapers',
        'orange_solver.py'
    )
    
    try:
        result = subprocess.run(
            ['python3', solver_path],
            capture_output=True,
            text=True,
            timeout=300
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
    print("=" * 60)
    print("Orange County Scraper -> Google Sheets")
    print("=" * 60)
    
    # Run scraper
    records = run_orange_scraper()
    
    if not records:
        print("No records to write")
        return
    
    # Write to Google Sheets
    print(f"\n📊 Writing {len(records)} records to Google Sheets...")
    stats = write_to_sheets(records, 'Orange')
    
    print(f"\n📈 Results:")
    print(f"   Total records: {stats['total']}")
    print(f"   New records written: {stats['new']}")
    print(f"   Duplicates skipped: {stats['skipped']}")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
