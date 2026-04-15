#!/usr/bin/env python3
"""
Escambia County Arrest Scraper
Target: https://myescambia.com/our-services/corrections/inmate-lookup
Stack: Python (requests + BeautifulSoup)
Status: 🟢 Active

Approach: Escambia uses a Revize CMS-powered search form. The search accepts
last name / first name and returns HTML table results. We search with empty
fields to get all current inmates, then parse the results table.
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


SEARCH_URL = "https://myescambia.com/our-services/corrections/inmate-lookup"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def scrape_escambia(days_back=7, max_pages=20):
    """
    Scrape Escambia County booking records.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum result pages to process

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Escambia County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    records = []
    page_num = 1

    # Step 1: Load the search page and try to get results
    try:
        # Try direct search with empty fields to get all inmates
        resp = session.get(SEARCH_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for the actual search form or iframe
        iframe = soup.find("iframe", src=True)
        if iframe:
            iframe_url = iframe["src"]
            if not iframe_url.startswith("http"):
                iframe_url = "https://myescambia.com" + iframe_url
            sys.stderr.write(f"📡 Found iframe, following: {iframe_url}\n")
            resp = session.get(iframe_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

        # Look for search form
        form = soup.find("form", action=True)
        if form:
            action = form.get("action", "")
            if not action.startswith("http"):
                action = "https://myescambia.com" + action

            # Collect all form fields (hidden + visible)
            form_data = {}
            for inp in form.find_all("input"):
                name = inp.get("name", "")
                value = inp.get("value", "")
                if name:
                    form_data[name] = value

            # Submit search with empty fields (get all)
            sys.stderr.write(f"📡 Submitting search form to {action}\n")
            resp = session.post(action, data=form_data, timeout=60)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

    except Exception as e:
        sys.stderr.write(f"❌ Error loading search page: {e}\n")
        return []

    # Step 2: Parse results
    while page_num <= max_pages:
        page_records = _parse_results_page(soup)

        if page_records:
            sys.stderr.write(f"📋 Page {page_num}: {len(page_records)} records\n")
            records.extend(page_records)
        else:
            if page_num == 1:
                sys.stderr.write("⚠️  No records found on first page — trying alternate parsing\n")
                # Try extracting from all table rows in the page
                alt_records = _parse_table_fallback(soup)
                if alt_records:
                    records.extend(alt_records)
                    sys.stderr.write(f"📋 Fallback found {len(alt_records)} records\n")
            break

        # Check for next page
        next_link = soup.find("a", string=re.compile(r"next|›|»", re.IGNORECASE))
        if not next_link or not next_link.get("href"):
            sys.stderr.write(f"🏁 No more pages after {page_num}\n")
            break

        next_url = next_link["href"]
        if not next_url.startswith("http"):
            next_url = "https://myescambia.com" + next_url

        try:
            resp = session.get(next_url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            sys.stderr.write(f"❌ Error fetching page {page_num + 1}: {e}\n")
            break

        page_num += 1
        time.sleep(1)

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _parse_results_page(soup):
    """Parse inmate records from a results page."""
    records = []

    # Method 1: Look for standard table with inmate data
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        # Check if this looks like an inmate table
        header_text = rows[0].get_text(strip=True).lower()
        if any(kw in header_text for kw in ["name", "booking", "inmate", "charge"]):
            headers = [td.get_text(strip=True).lower() for td in rows[0].find_all(["th", "td"])]
            for row in rows[1:]:
                record = _row_to_record(row, headers)
                if record:
                    records.append(record)
            if records:
                return records

    # Method 2: Look for card/div-based layout
    cards = soup.find_all("div", class_=re.compile(r"inmate|result|record|card", re.IGNORECASE))
    for card in cards:
        record = _card_to_record(card)
        if record:
            records.append(record)

    # Method 3: Look for definition lists (dl/dt/dd)
    dls = soup.find_all("dl")
    for dl in dls:
        record = _dl_to_record(dl)
        if record:
            records.append(record)

    return records


def _row_to_record(row, headers):
    """Convert a table row to a record dict using header column mapping."""
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    texts = [c.get_text(strip=True) for c in cells]
    record = {
        "County": "Escambia",
        "State": "FL",
        "Facility": "Escambia County Jail",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    for i, header in enumerate(headers):
        if i >= len(texts):
            break
        val = texts[i]
        if not val:
            continue

        if "last" in header and "name" in header:
            record["Last_Name"] = val
        elif "first" in header and "name" in header:
            record["First_Name"] = val
        elif "name" in header:
            record["Full_Name"] = val
        elif "book" in header and ("no" in header or "num" in header or "#" in header or "id" in header):
            record["Booking_Number"] = val
        elif "book" in header and "date" in header:
            record["Booking_Date"] = val
        elif "charge" in header or "offense" in header:
            record["Charges"] = val
        elif "bond" in header:
            cleaned = re.sub(r'[^\d.]', '', val)
            if cleaned:
                record["Bond_Amount"] = cleaned
        elif "dob" in header or "birth" in header:
            record["DOB"] = val
        elif "sex" in header or "gender" in header:
            record["Sex"] = val
        elif "race" in header:
            record["Race"] = val
        elif "release" in header:
            record["Release_Date"] = val
        elif "arrest" in header and "date" in header:
            record["Booking_Date"] = val

    # Build full name
    if not record.get("Full_Name"):
        parts = []
        if record.get("Last_Name"):
            parts.append(record["Last_Name"])
        if record.get("First_Name"):
            parts.append(record["First_Name"])
        if parts:
            record["Full_Name"] = ", ".join(parts)

    if record.get("Full_Name") and not record.get("Last_Name"):
        name = record["Full_Name"]
        if "," in name:
            p = name.split(",", 1)
            record["Last_Name"] = p[0].strip()
            record["First_Name"] = p[1].strip()

    # Check for detail link
    link = row.find("a", href=True)
    if link:
        href = link["href"]
        if not href.startswith("http"):
            href = "https://myescambia.com" + href
        record["Detail_URL"] = href

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _card_to_record(card):
    """Parse a card/div element into a record."""
    text = card.get_text(" ", strip=True)
    if len(text) < 10:
        return None

    record = {
        "County": "Escambia",
        "State": "FL",
        "Facility": "Escambia County Jail",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Try label: value pattern
    for line in text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip()
            if "name" in key:
                record["Full_Name"] = val
            elif "booking" in key:
                record["Booking_Number"] = val
            elif "charge" in key:
                record["Charges"] = val
            elif "bond" in key:
                cleaned = re.sub(r'[^\d.]', '', val)
                if cleaned:
                    record["Bond_Amount"] = cleaned

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _dl_to_record(dl):
    """Parse a definition list into a record."""
    record = {
        "County": "Escambia",
        "State": "FL",
        "Facility": "Escambia County Jail",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    dts = dl.find_all("dt")
    dds = dl.find_all("dd")

    for dt, dd in zip(dts, dds):
        key = dt.get_text(strip=True).lower()
        val = dd.get_text(strip=True)
        if "name" in key:
            record["Full_Name"] = val
        elif "booking" in key:
            record["Booking_Number"] = val
        elif "charge" in key:
            record["Charges"] = val

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _parse_table_fallback(soup):
    """Fallback: find any table with enough rows and parse it."""
    records = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if len(rows) < 3:
            continue

        headers = [td.get_text(strip=True).lower() for td in rows[0].find_all(["th", "td"])]
        for row in rows[1:]:
            record = _row_to_record(row, headers)
            if record:
                records.append(record)
    return records


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Escambia County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_escambia(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
