#!/usr/bin/env python3
"""
Alachua County Arrest Scraper
Target: https://asosite.alachuasheriff.org/ASOInmateLookup.aspx
Stack: Python (requests + BeautifulSoup)
Status: 🟢 Active

Approach: ASP.NET WebForms with "View All" button.
POST the form with ButtonView=View All + __VIEWSTATE token → parse GridView table.
"""

import sys
import json
import time
import re
from datetime import datetime, timedelta

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("❌ Missing deps: pip install requests beautifulsoup4\n")
    sys.exit(1)


BASE_URL = "https://asosite.alachuasheriff.org/ASOInmateLookup.aspx"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
}


def scrape_alachua(days_back=7, max_pages=20):
    """
    Scrape Alachua County booking records.

    Args:
        days_back: Number of days to look back (filters after scraping)
        max_pages: Maximum pages (unused — single View All page)

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Alachua County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Step 1: GET the search page to harvest ASP.NET tokens
    try:
        home = session.get(BASE_URL, timeout=30)
        home.raise_for_status()
    except Exception as e:
        sys.stderr.write(f"❌ Failed to load search page: {e}\n")
        return []

    soup = BeautifulSoup(home.text, "html.parser")

    # Extract ASP.NET hidden fields
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"name": "__EVENTVALIDATION"})

    if not viewstate or not event_validation:
        sys.stderr.write("❌ Could not find ASP.NET form tokens\n")
        return []

    form_data = {
        "__VIEWSTATE": viewstate.get("value", ""),
        "__VIEWSTATEGENERATOR": viewstate_gen.get("value", "") if viewstate_gen else "",
        "__VIEWSTATEENCRYPTED": "",
        "__EVENTVALIDATION": event_validation.get("value", ""),
        "txtLName": "",
        "txtFName": "",
        "txtBookNo": "",
        "ButtonView": "View All",  # The "View All" button
    }

    sys.stderr.write("📡 Submitting 'View All' search...\n")

    try:
        resp = session.post(BASE_URL, data=form_data, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        sys.stderr.write(f"❌ Search POST failed: {e}\n")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")

    # Step 2: Parse the GridView table
    records = []
    cutoff_date = datetime.now() - timedelta(days=days_back)

    # Find the main data grid — ASP.NET typically renders as a table with class="Grid"
    # or we look for any table with multiple rows
    tables = soup.find_all("table")
    data_table = None

    for table in tables:
        rows = table.find_all("tr")
        if len(rows) > 3:  # Header + at least a few data rows
            data_table = table
            break

    if not data_table:
        # Try finding by GridView ID pattern
        data_table = soup.find("table", id=re.compile(r"GridView|gv|grid", re.IGNORECASE))

    if not data_table:
        sys.stderr.write("⚠️  No data table found in response\n")
        # Check if results are in a different format (expandable rows with +/- icons)
        # The page uses jQuery expand/collapse with plus.gif/minus.gif
        all_rows = soup.find_all("tr")
        if all_rows:
            sys.stderr.write(f"   Found {len(all_rows)} total <tr> elements, attempting parse...\n")
            data_table = soup  # parse all rows in the page
        else:
            return []

    rows = data_table.find_all("tr")
    sys.stderr.write(f"📋 Found {len(rows)} rows in data table\n")

    # Skip header row
    header_cells = rows[0].find_all(["th", "td"]) if rows else []
    headers = [c.get_text(strip=True).lower() for c in header_cells]
    sys.stderr.write(f"   Headers: {headers}\n")

    # Build column index map
    col_map = {}
    for i, h in enumerate(headers):
        if "name" in h and "last" in h:
            col_map["last_name"] = i
        elif "name" in h and "first" in h:
            col_map["first_name"] = i
        elif "name" in h:
            col_map["name"] = i
        elif "book" in h and ("no" in h or "num" in h or "#" in h):
            col_map["booking_number"] = i
        elif "book" in h and "date" in h:
            col_map["booking_date"] = i
        elif "charge" in h:
            col_map["charges"] = i
        elif "bond" in h:
            col_map["bond"] = i
        elif "dob" in h or "birth" in h:
            col_map["dob"] = i
        elif "sex" in h or "gender" in h:
            col_map["sex"] = i
        elif "race" in h:
            col_map["race"] = i
        elif "release" in h:
            col_map["release_date"] = i

    for row in rows[1:]:  # Skip header
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        texts = [c.get_text(strip=True) for c in cells]

        record = {
            "County": "Alachua",
            "State": "FL",
            "Facility": "Alachua County Jail",
            "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Map cells to fields using header positions
        if "last_name" in col_map and col_map["last_name"] < len(texts):
            record["Last_Name"] = texts[col_map["last_name"]]
        if "first_name" in col_map and col_map["first_name"] < len(texts):
            record["First_Name"] = texts[col_map["first_name"]]
        if "name" in col_map and col_map["name"] < len(texts):
            record["Full_Name"] = texts[col_map["name"]]
        if "booking_number" in col_map and col_map["booking_number"] < len(texts):
            record["Booking_Number"] = texts[col_map["booking_number"]]
        if "booking_date" in col_map and col_map["booking_date"] < len(texts):
            record["Booking_Date"] = texts[col_map["booking_date"]]
        if "charges" in col_map and col_map["charges"] < len(texts):
            record["Charges"] = texts[col_map["charges"]]
        if "bond" in col_map and col_map["bond"] < len(texts):
            raw_bond = texts[col_map["bond"]]
            cleaned = re.sub(r'[^\d.]', '', raw_bond)
            if cleaned:
                record["Bond_Amount"] = cleaned
        if "dob" in col_map and col_map["dob"] < len(texts):
            record["DOB"] = texts[col_map["dob"]]
        if "sex" in col_map and col_map["sex"] < len(texts):
            record["Sex"] = texts[col_map["sex"]]
        if "race" in col_map and col_map["race"] < len(texts):
            record["Race"] = texts[col_map["race"]]
        if "release_date" in col_map and col_map["release_date"] < len(texts):
            record["Release_Date"] = texts[col_map["release_date"]]

        # If no column map matched, try positional fallback
        if not col_map and len(texts) >= 3:
            record["Full_Name"] = texts[0]
            record["Booking_Number"] = texts[1] if len(texts) > 1 else ""
            record["Booking_Date"] = texts[2] if len(texts) > 2 else ""
            if len(texts) > 3:
                record["Charges"] = texts[3]

        # Build Full_Name from parts if not set
        if not record.get("Full_Name"):
            parts = []
            if record.get("Last_Name"):
                parts.append(record["Last_Name"])
            if record.get("First_Name"):
                parts.append(record["First_Name"])
            if parts:
                record["Full_Name"] = ", ".join(parts)

        # Parse Full_Name into parts if needed
        if record.get("Full_Name") and not record.get("Last_Name"):
            name = record["Full_Name"]
            if "," in name:
                parts = name.split(",", 1)
                record["Last_Name"] = parts[0].strip()
                record["First_Name"] = parts[1].strip()

        # Check for expandable detail rows (the +/- icon pattern)
        expand_panel = row.find("div", style=re.compile(r"display", re.IGNORECASE))
        if expand_panel:
            detail_text = expand_panel.get_text(" ", strip=True)
            # Try to extract charges from detail
            charge_match = re.findall(r'(?:Charge|Offense)[:\s]*(.+?)(?:Bond|$)', detail_text, re.IGNORECASE)
            if charge_match and not record.get("Charges"):
                record["Charges"] = " | ".join(c.strip() for c in charge_match)

        # Only add if we have identifying info
        if record.get("Full_Name") or record.get("Booking_Number"):
            records.append(record)

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Alachua County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_alachua(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
