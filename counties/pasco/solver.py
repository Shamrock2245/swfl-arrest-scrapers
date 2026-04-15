#!/usr/bin/env python3
"""
Pasco County Arrest Scraper
Target: https://www.pascocountyfl.gov (Corrections / Inmate Services)
Stack: Python (DrissionPage — Cloudflare protected)
Status: 🟢 Active

Approach: Pasco's site returns 403 to raw HTTP requests (Cloudflare).
We use DrissionPage to:
1. Load the page through Cloudflare
2. Navigate to the inmate search
3. Submit search form for all current inmates
4. Parse results table
"""

import sys
import json
import os
import time
import re
from datetime import datetime, timedelta

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    HAS_DRISSION = True
except ImportError:
    HAS_DRISSION = False
    sys.stderr.write("⚠️  DrissionPage not installed\n")


SEARCH_URL = "https://www.pascocountyfl.gov/government/public_safety_justice/corrections/inmate_services"


def setup_browser(headed=False):
    """Configure and return a DrissionPage browser instance."""
    co = ChromiumOptions()
    co.auto_port()

    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        co.set_browser_path(chrome_path)

    if not headed:
        co.headless(True)
        co.set_argument('--headless=new')

    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--window-size=1920,1080')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    return ChromiumPage(addr_or_opts=co)


def wait_for_cloudflare(page, max_wait=30):
    """Wait for Cloudflare challenge to clear."""
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ''
        html = page.html[:500].lower() if page.html else ''
        if 'just a moment' not in title and 'checking' not in title and 'challenge' not in html:
            return True
        sys.stderr.write(f"   ⏳ Waiting for Cloudflare ({waited}s)...\n")
        time.sleep(1)
        waited += 1
    return False


def scrape_pasco(days_back=7, max_pages=20):
    """
    Scrape Pasco County booking records.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum result pages

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Pasco County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    if not HAS_DRISSION:
        sys.stderr.write("❌ DrissionPage required for Pasco County (Cloudflare)\n")
        return []

    page = setup_browser()
    records = []

    try:
        # Step 1: Navigate through Cloudflare
        sys.stderr.write("📡 Loading Pasco County corrections page...\n")
        page.get(SEARCH_URL)
        time.sleep(3)

        if not wait_for_cloudflare(page):
            sys.stderr.write("❌ Cloudflare challenge did not clear\n")
            return []

        sys.stderr.write(f"📡 Page loaded: {page.title}\n")

        # Step 2: Find links to inmate search
        # Look for "In Custody" or "Past Arrests" links
        search_links = []
        for link_text in ["In Custody", "Current Inmates", "Inmate Search", "Past Arrests", "Arrest Inquiry"]:
            try:
                link = page.ele(f'tag:a@@text():{link_text}', timeout=3)
                if link:
                    search_links.append((link_text, link))
                    sys.stderr.write(f"   Found link: {link_text}\n")
            except Exception:
                continue

        if not search_links:
            # Try to find any iframe containing the search
            try:
                iframe = page.ele('tag:iframe', timeout=3)
                if iframe:
                    iframe_src = iframe.attr('src')
                    sys.stderr.write(f"   Found iframe: {iframe_src}\n")
                    page.get(iframe_src)
                    time.sleep(3)
            except Exception:
                pass

        # Click the first search link found
        if search_links:
            link_text, link = search_links[0]
            sys.stderr.write(f"📡 Clicking '{link_text}' link...\n")
            link.click()
            time.sleep(5)
            wait_for_cloudflare(page)

        # Step 3: Look for search form and submit
        try:
            # Try to find and submit a search form
            search_btn = page.ele('tag:button@@text():Search', timeout=5) or \
                         page.ele('tag:input@@type=submit', timeout=3) or \
                         page.ele('tag:button@@type=submit', timeout=3)
            if search_btn:
                sys.stderr.write("📡 Submitting search form...\n")
                search_btn.click()
                time.sleep(5)
        except Exception as e:
            sys.stderr.write(f"   ⚠️  No search form found: {e}\n")

        # Step 4: Parse results from the page
        sys.stderr.write("📡 Parsing results...\n")

        # Parse the rendered HTML
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.html, "html.parser")

        # Find tables with inmate data
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            # Get headers
            header_row = rows[0]
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(["th", "td"])]

            if not any(kw in " ".join(headers) for kw in ["name", "inmate", "booking", "arrest"]):
                continue

            sys.stderr.write(f"📋 Found data table with {len(rows) - 1} rows\n")
            sys.stderr.write(f"   Headers: {headers}\n")

            for row in rows[1:]:
                record = _parse_row(row, headers)
                if record:
                    records.append(record)

        # If no table found, try other patterns
        if not records:
            # Look for listing cards/divs
            cards = soup.find_all("div", class_=re.compile(r"inmate|result|record|list-item", re.IGNORECASE))
            for card in cards:
                record = _parse_card(card)
                if record:
                    records.append(record)

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
    finally:
        try:
            page.quit()
        except Exception:
            pass

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _parse_row(row, headers):
    """Parse a table row into a record dict."""
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    texts = [c.get_text(strip=True) for c in cells]

    record = {
        "County": "Pasco",
        "State": "FL",
        "Facility": "Pasco County Detention Center",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    for i, header in enumerate(headers):
        if i >= len(texts) or not texts[i]:
            continue
        val = texts[i]

        if "last" in header and "name" in header:
            record["Last_Name"] = val
        elif "first" in header and "name" in header:
            record["First_Name"] = val
        elif "name" in header:
            record["Full_Name"] = val
        elif "book" in header and ("no" in header or "num" in header or "#" in header):
            record["Booking_Number"] = val
        elif "book" in header and "date" in header:
            record["Booking_Date"] = val
        elif "arrest" in header and "date" in header:
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
        if "," in record["Full_Name"]:
            p = record["Full_Name"].split(",", 1)
            record["Last_Name"] = p[0].strip()
            record["First_Name"] = p[1].strip()

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _parse_card(card):
    """Parse a div/card element into a record."""
    text = card.get_text(" ", strip=True)
    if len(text) < 10:
        return None

    record = {
        "County": "Pasco",
        "State": "FL",
        "Facility": "Pasco County Detention Center",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pasco County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_pasco(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
