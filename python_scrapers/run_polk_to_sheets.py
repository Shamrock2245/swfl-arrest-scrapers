#!/usr/bin/env python3
"""
Polk County Scraper Runner - Scrapes and writes to Google Sheets

This script:
1. Runs the Polk County scraper
2. Writes new records to the Polk sheet using SimpleSheetsWriter
"""

import sys
import os
import time

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_scrapers.scrapers.polk_solver import setup_browser, search_by_name, COMMON_LAST_NAMES
from python_scrapers.writers.simple_sheets_writer import SimpleSheetsWriter

POLK_SHEET_NAME = 'Polk'


def run_polk_scraper_to_sheets(max_names=50):
    """
    Run the Polk County scraper and write results to Google Sheets.
    
    Args:
        max_names: Maximum number of common names to search
    """
    print("=" * 60)
    print("POLK COUNTY SCRAPER TO SHEETS")
    print("=" * 60)
    
    # Initialize sheets writer
    print("\n📊 Initializing Google Sheets connection...")
    writer = SimpleSheetsWriter()
    
    # Get existing booking numbers to avoid duplicates
    print("📋 Fetching existing records from Polk sheet...")
    existing_bookings = writer.get_existing_booking_numbers(POLK_SHEET_NAME)
    print(f"   Found {len(existing_bookings)} existing records")
    
    # Run the scraper
    print("\n🔵 Starting Polk County scraper...")
    
    url = "https://www.polksheriff.org/detention/jail-inquiry"
    all_records = []
    seen_bookings = set()
    driver = None
    
    try:
        print(f"📡 Launching browser and navigating to {url}...")
        driver = setup_browser()
        driver.get(url)
        time.sleep(5)
        
        # Search by common last names
        names_to_search = COMMON_LAST_NAMES[:max_names]
        print(f"🔍 Searching {len(names_to_search)} common last names for current inmates...")
        
        for i, name in enumerate(names_to_search):
            print(f"   [{i+1}/{len(names_to_search)}] Searching '{name}'...", end='', flush=True)
            
            # Refresh page to reset state
            driver.get(url)
            time.sleep(3)
            
            records = search_by_name(driver, name, current_only=True)
            
            # Deduplicate by booking number
            new_count = 0
            for record in records:
                booking_num = record.get('Booking_Number', '')
                if booking_num and booking_num not in seen_bookings:
                    seen_bookings.add(booking_num)
                    all_records.append(record)
                    new_count += 1
            
            print(f" {len(records)} found ({new_count} new)")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
    
    print(f"\n📊 Scraped {len(all_records)} total unique records")
    
    if all_records:
        # Write to sheets using SimpleSheetsWriter (handles deduplication)
        print(f"\n✍️ Writing records to Google Sheets...")
        stats = writer.write_records(all_records, POLK_SHEET_NAME, deduplicate=True)
        print(f"✅ Results: {stats['new']} new, {stats['skipped']} skipped")
    else:
        print("ℹ️ No records to write")
    
    print("\n" + "=" * 60)
    print("POLK COUNTY SCRAPER COMPLETE")
    print("=" * 60)
    
    return len(all_records)


if __name__ == "__main__":
    # Default to searching 50 common names
    max_names = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    run_polk_scraper_to_sheets(max_names=max_names)
