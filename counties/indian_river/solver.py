#!/usr/bin/env python3
"""
Indian River County Arrest Scraper
Target: https://www.ircsheriff.org/inmate-search
Stack: Python (requests + BeautifulSoup)
Status: 🟢 Active

Approach: The inmate search page renders HTML directly with booking links
at /booking-details/{id}. Parse listing page for links, then fetch detail pages.
Today's and yesterday's bookings are listed directly on the page.
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
    Each booking links to /booking-details/{id} with full detail.

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
    booking_urls = set()

    # Fetch both the main search page and today's bookings
    for page_url in [SEARCH_URL, TODAYS_URL]:
        try:
            sys.stderr.write(f"📡 Loading: {page_url}\n")
            resp = session.get(page_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Find all booking detail links
            links = soup.find_all("a", href=re.compile(r"/booking-details/\d+"))
            for link in links:
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = BASE_URL + href
                booking_urls.add(href)

                # Also extract listing-level data
                name = link.get_text(strip=True)
                if name:
                    # Find parent container for DOB, bond, status
                    parent = link.find_parent("li") or link.find_parent("div")
                    listing_data = {
                        "Full_Name": name,
                        "Detail_URL": href,
                    }
                    if parent:
                        parent_text = parent.get_text()
                        # Extract DOB from listing
                        dob_match = re.search(r"DOB:\s*(\d{2}/\d{2}/\d{4})", parent_text)
                        if dob_match:
                            listing_data["DOB"] = dob_match.group(1)
                        # Extract bond
                        bond_match = re.search(r"Bond:\s*\$?([\d,]+\.?\d*)", parent_text)
                        if bond_match:
                            listing_data["Bond_Amount"] = bond_match.group(1).replace(",", "")
                        # Extract status
                        if "Incarcerated" in parent_text:
                            listing_data["Status"] = "Incarcerated"
                        elif "Released" in parent_text:
                            listing_data["Status"] = "Released"

            sys.stderr.write(f"   Found {len(links)} booking links\n")

        except Exception as e:
            sys.stderr.write(f"❌ Error loading {page_url}: {e}\n")

    sys.stderr.write(f"📋 Total unique booking URLs: {len(booking_urls)}\n")

    # Fetch detail pages
    for i, url in enumerate(list(booking_urls)[:max_pages * 10]):
        try:
            sys.stderr.write(f"🔍 [{i+1}/{len(booking_urls)}] Fetching: {url}\n")
            record = _fetch_booking_detail(session, url)
            if record:
                records.append(record)
            time.sleep(0.5)  # Be polite
        except Exception as e:
            sys.stderr.write(f"   ⚠️  Error: {e}\n")

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _fetch_booking_detail(session, url):
    """Fetch an individual booking detail page and extract data."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        record = {
            "County": "Indian River",
            "State": "FL",
            "Facility": "Indian River County Jail",
            "Detail_URL": url,
        }

        # Extract booking ID from URL
        id_match = re.search(r"/booking-details/(\d+)", url)
        if id_match:
            record["Booking_Number"] = id_match.group(1)

        # Extract name — typically in h1 or h2
        name_el = soup.find("h1") or soup.find("h2")
        if name_el:
            name = name_el.get_text(strip=True)
            # Skip if it's the page title
            if name and "booking" not in name.lower() and "inmate" not in name.lower():
                record["Full_Name"] = name
                if "," in name:
                    parts = name.split(",", 1)
                    record["Last_Name"] = parts[0].strip()
                    record["First_Name"] = parts[1].strip()

        # Generic label:value extraction
        def get_field(labels):
            for label_text in labels:
                # Try finding text containing label
                for el in soup.find_all(string=re.compile(label_text, re.IGNORECASE)):
                    parent = el.parent
                    if parent:
                        full = parent.get_text(strip=True)
                        parts = re.split(r':\s*', full, maxsplit=1)
                        if len(parts) > 1 and parts[1].strip():
                            return parts[1].strip()
                        next_el = parent.find_next_sibling()
                        if next_el:
                            return next_el.get_text(strip=True)
                # Try table row approach
                for td in soup.find_all("td"):
                    if label_text.lower() in td.get_text(strip=True).lower():
                        next_td = td.find_next_sibling("td")
                        if next_td:
                            return next_td.get_text(strip=True)
                # Try dt/dd approach
                for dt in soup.find_all("dt"):
                    if label_text.lower() in dt.get_text(strip=True).lower():
                        dd = dt.find_next_sibling("dd")
                        if dd:
                            return dd.get_text(strip=True)
            return None

        record["Booking_Date"] = get_field(["Booking Date", "Book Date", "Arrest Date", "Date Booked"])
        record["DOB"] = get_field(["Date of Birth", "DOB", "Birth Date"])
        record["Sex"] = get_field(["Gender", "Sex"])
        record["Race"] = get_field(["Race", "Ethnicity"])
        record["Height"] = get_field(["Height"])
        record["Weight"] = get_field(["Weight"])
        record["Address"] = get_field(["Address", "Home Address", "Residence"])
        record["Hair_Color"] = get_field(["Hair", "Hair Color"])
        record["Eye_Color"] = get_field(["Eye", "Eye Color"])

        # Extract charges
        charges = []
        charge_sections = soup.find_all(string=re.compile(r"charge|offense|statute", re.IGNORECASE))
        charge_tables = soup.select("table.charges, .charge-row, [class*='charge']")
        for ct in charge_tables:
            rows = ct.find_all("tr") if ct.name == "table" else [ct]
            for row in rows:
                text = row.get_text(strip=True)
                if text and len(text) > 5 and not text.startswith("Charge"):
                    charges.append(text)
        if charges:
            record["Charges"] = " | ".join(charges[:10])  # Cap at 10 charges

        # Bond amount
        bond = get_field(["Bond Amount", "Bond", "Total Bond"])
        if bond:
            cleaned = re.sub(r'[^\d.]', '', bond)
            if cleaned:
                record["Bond_Amount"] = cleaned

        # Mugshot
        mugshot = soup.find("img", {"src": re.compile(r"photo|mugshot|inmate|booking", re.IGNORECASE)})
        if mugshot and mugshot.get("src"):
            src = mugshot["src"]
            if not src.startswith("http"):
                src = BASE_URL + src
            record["Mugshot_URL"] = src

        # Remove None values
        record = {k: v for k, v in record.items() if v is not None}

        if record.get("Full_Name") or record.get("Booking_Number"):
            sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')} ({record.get('Booking_Number', 'N/A')})\n")
            return record

    except Exception as e:
        sys.stderr.write(f"   ⚠️  Detail error: {e}\n")
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Indian River County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=3)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    records = scrape_indian_river(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
