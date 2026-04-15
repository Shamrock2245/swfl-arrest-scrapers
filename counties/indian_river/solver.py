#!/usr/bin/env python3
"""
Indian River County Arrest Scraper
Target: https://www.ircsheriff.org/inmate-search
Stack: Python (requests + BeautifulSoup)
Status: 🟢 Active

Approach:
  The inmate search page renders Today's and Yesterday's bookings as
  static HTML with name, DOB, bond, and booking-detail links.
  Detail pages are JavaScript-rendered (React SPA) so we extract all
  available data from the listing page directly rather than fetching
  individual detail URLs that return empty shells.
"""

import sys
import json
import time
import re
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("❌ Missing deps: pip install requests beautifulsoup4\n")
    sys.exit(1)


BASE_URL = "https://www.ircsheriff.org"
SEARCH_URL = f"{BASE_URL}/inmate-search"
TODAYS_URL = f"{BASE_URL}/todays-bookings"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_indian_river(days_back=3, max_pages=10):
    """
    Scrape Indian River County booking records.

    The site shows today's and yesterday's bookings at /inmate-search.
    Data is extracted from the listing page since detail pages require
    JavaScript rendering.

    Args:
        days_back: Not used (site only shows recent bookings)
        max_pages: Max detail pages to fetch

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Indian River County Scraper\n")
    sys.stderr.write(f"📅 Fetching recent bookings\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    records = []
    seen_ids = set()

    # Fetch both the main search page and today's bookings
    for page_url in [SEARCH_URL, TODAYS_URL]:
        try:
            sys.stderr.write(f"📡 Loading: {page_url}\n")
            resp = session.get(page_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Find all booking detail links
            links = soup.find_all("a", href=re.compile(r"/booking-details/\d+"))
            sys.stderr.write(f"   Found {len(links)} booking links\n")

            for link in links:
                href = link.get("href", "")
                # Extract booking ID
                id_match = re.search(r"/booking-details/(\d+)", href)
                if not id_match:
                    continue
                booking_id = id_match.group(1)

                # Deduplicate across pages
                if booking_id in seen_ids:
                    continue
                seen_ids.add(booking_id)

                # Extract name from link text
                name = link.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Build detail URL
                detail_url = href if href.startswith("http") else BASE_URL + href

                # Initialize record from listing data
                record = {
                    "County": "Indian River",
                    "State": "FL",
                    "Facility": "Indian River County Jail",
                    "Full_Name": name,
                    "Booking_Number": booking_id,
                    "Detail_URL": detail_url,
                }

                # Parse name parts (site uses "Last, First Middle" format)
                if "," in name:
                    parts = name.split(",", 1)
                    record["Last_Name"] = parts[0].strip()
                    first_parts = parts[1].strip().split()
                    if first_parts:
                        record["First_Name"] = first_parts[0]
                    if len(first_parts) > 1:
                        record["Middle_Name"] = " ".join(first_parts[1:])

                # Find parent list item for context data (DOB, bond, status)
                parent = link.find_parent("li") or link.find_parent("div")
                if parent:
                    parent_text = parent.get_text(separator=" ", strip=True)

                    # Extract DOB
                    dob_match = re.search(r"DOB:\s*(\d{2}/\d{2}/\d{4})", parent_text)
                    if dob_match:
                        record["DOB"] = dob_match.group(1)

                    # Extract Bond Amount
                    bond_match = re.search(r"Bond:\s*\$?([\d,]+\.?\d*)", parent_text)
                    if bond_match:
                        record["Bond_Amount"] = bond_match.group(1).replace(",", "")
                    elif "No Bond" in parent_text:
                        record["Bond_Amount"] = "0"
                        record["Bond_Type"] = "No Bond"

                    # Extract status
                    if "Incarcerated" in parent_text:
                        record["Status"] = "Incarcerated"
                    elif "Released" in parent_text:
                        record["Status"] = "Released"

                    # Extract booking count
                    bookings_match = re.search(r"Bookings:\s*(\d+)", parent_text)
                    if bookings_match:
                        record["Person_ID"] = f"IRC-{booking_id}-B{bookings_match.group(1)}"

                # Set timestamps
                record["Scrape_Timestamp"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                records.append(record)
                sys.stderr.write(f"   ✅ {name} (#{booking_id})\n")

        except requests.RequestException as e:
            sys.stderr.write(f"❌ HTTP error loading {page_url}: {e}\n")
        except Exception as e:
            sys.stderr.write(f"❌ Error loading {page_url}: {e}\n")

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Indian River County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    records = scrape_indian_river(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
