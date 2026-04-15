#!/usr/bin/env python3
"""
Duval County (Jacksonville) Arrest Scraper
Target: https://inmatesearch.jaxsheriff.org
Stack: Python (DrissionPage — Angular SPA requires browser)
Status: 🟢 Active

Approach: The site is an Angular SPA (<wic-root>). We use DrissionPage to:
1. Load the page and wait for Angular to render
2. Intercept the API calls the frontend makes
3. Parse the JSON response directly (far more reliable than DOM scraping)
If API intercept fails, fall back to DOM scraping.
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
    sys.stderr.write("⚠️  DrissionPage not installed — will attempt requests fallback\n")


BASE_URL = "https://inmatesearch.jaxsheriff.org"


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


def scrape_duval(days_back=7, max_pages=20):
    """
    Scrape Duval County booking records.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum pages to process

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Duval County (Jacksonville) Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    if not HAS_DRISSION:
        sys.stderr.write("❌ DrissionPage required for Duval County (Angular SPA)\n")
        return []

    page = setup_browser()
    records = []

    try:
        # Step 1: Navigate and listen for API calls
        sys.stderr.write("📡 Loading Angular SPA...\n")

        # Start listening for API requests before navigating
        page.listen.start('api')
        page.get(BASE_URL)
        time.sleep(5)  # Wait for Angular to bootstrap

        sys.stderr.write(f"📡 Page title: {page.title}\n")

        # Step 2: Try to trigger a search
        # Look for search inputs and submit
        try:
            # Try clicking a "Search" or "View All" button
            search_btn = page.ele('tag:button@@text():Search', timeout=5)
            if search_btn:
                search_btn.click()
                time.sleep(3)
            else:
                # Try submit button
                submit_btn = page.ele('tag:button@@type=submit', timeout=3)
                if submit_btn:
                    submit_btn.click()
                    time.sleep(3)
        except Exception as e:
            sys.stderr.write(f"   ⚠️  No search button found, trying direct navigation: {e}\n")

        # Step 3: Try to intercept API responses
        api_data = None
        try:
            packets = page.listen.wait(timeout=10, count=5)
            if packets:
                for packet in ([packets] if not isinstance(packets, list) else packets):
                    try:
                        body = packet.response.body
                        if isinstance(body, (dict, list)):
                            if isinstance(body, list) and len(body) > 0:
                                api_data = body
                                sys.stderr.write(f"📡 Intercepted API response: {len(body)} records\n")
                                break
                            elif isinstance(body, dict):
                                # Check for common API response structures
                                for key in ['data', 'results', 'inmates', 'records', 'items']:
                                    if key in body and isinstance(body[key], list):
                                        api_data = body[key]
                                        sys.stderr.write(f"📡 Intercepted API response [{key}]: {len(api_data)} records\n")
                                        break
                    except Exception:
                        continue
        except Exception as e:
            sys.stderr.write(f"   ⚠️  API intercept failed: {e}\n")

        # Step 4: Parse API data if available
        if api_data:
            for item in api_data:
                record = _api_item_to_record(item)
                if record:
                    records.append(record)
        else:
            # Step 5: Fall back to DOM scraping
            sys.stderr.write("📡 Falling back to DOM scraping...\n")
            records = _scrape_dom(page, max_pages)

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
    finally:
        try:
            page.quit()
        except Exception:
            pass

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _api_item_to_record(item):
    """Convert an API response item to a standard record dict."""
    if not isinstance(item, dict):
        return None

    record = {
        "County": "Duval",
        "State": "FL",
        "Facility": "Duval County Jail",
        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Map common API field names to our schema
    field_maps = {
        "Full_Name": ["name", "fullName", "full_name", "inmateFullName", "inmateName", "Name", "FullName"],
        "First_Name": ["firstName", "first_name", "fname", "FirstName"],
        "Last_Name": ["lastName", "last_name", "lname", "LastName"],
        "Booking_Number": ["bookingNumber", "booking_number", "bookingNo", "bookNum", "BookingNumber", "BookNumber"],
        "Booking_Date": ["bookingDate", "booking_date", "bookDate", "arrestDate", "BookingDate", "ArrestDate"],
        "DOB": ["dateOfBirth", "dob", "birthDate", "DOB", "DateOfBirth"],
        "Sex": ["sex", "gender", "Sex", "Gender"],
        "Race": ["race", "ethnicity", "Race"],
        "Charges": ["charges", "charge", "offenseDescription", "Charges", "ChargeDescription"],
        "Bond_Amount": ["bondAmount", "bond_amount", "totalBond", "bond", "BondAmount", "TotalBond"],
        "Release_Date": ["releaseDate", "release_date", "ReleaseDate"],
        "Mugshot_URL": ["photoUrl", "mugshot", "photo", "imageUrl", "PhotoUrl", "MugshotUrl"],
        "Address": ["address", "homeAddress", "Address"],
    }

    for our_field, api_fields in field_maps.items():
        for api_field in api_fields:
            if api_field in item and item[api_field]:
                record[our_field] = str(item[api_field]).strip()
                break

    # Handle charges if they come as an array
    if "charges" in item and isinstance(item["charges"], list):
        charge_texts = []
        for charge in item["charges"]:
            if isinstance(charge, dict):
                desc = charge.get("description", charge.get("chargeDescription", charge.get("offense", "")))
                if desc:
                    charge_texts.append(str(desc).strip())
            elif isinstance(charge, str):
                charge_texts.append(charge.strip())
        if charge_texts:
            record["Charges"] = " | ".join(charge_texts)

    # Build Full_Name if not present
    if not record.get("Full_Name"):
        parts = []
        if record.get("Last_Name"):
            parts.append(record["Last_Name"])
        if record.get("First_Name"):
            parts.append(record["First_Name"])
        if parts:
            record["Full_Name"] = ", ".join(parts)

    # Clean bond amount
    if record.get("Bond_Amount"):
        cleaned = re.sub(r'[^\d.]', '', str(record["Bond_Amount"]))
        record["Bond_Amount"] = cleaned if cleaned else ""

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _scrape_dom(page, max_pages):
    """Fall back to scraping the rendered DOM."""
    records = []

    for pg in range(max_pages):
        # Find inmate rows/cards in the rendered DOM
        rows = page.eles('tag:tr') or []
        cards = page.eles('css:.inmate-row,.result-row,.mat-row,[class*=inmate]') or []

        elements = cards if cards else rows
        sys.stderr.write(f"   Page {pg + 1}: {len(elements)} elements found\n")

        if not elements and pg == 0:
            # Try getting all text and parsing it
            body_text = page.html
            soup_records = _parse_html_fallback(body_text)
            records.extend(soup_records)
            break

        for el in elements:
            try:
                text = el.text.strip()
                if len(text) < 5:
                    continue

                record = {
                    "County": "Duval",
                    "State": "FL",
                    "Facility": "Duval County Jail",
                    "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                # Try to extract structured data from the element
                cells = el.eles('tag:td')
                if cells and len(cells) >= 2:
                    texts = [c.text.strip() for c in cells]
                    if texts[0]:
                        record["Full_Name"] = texts[0]
                    if len(texts) > 1 and texts[1]:
                        record["Booking_Number"] = texts[1]
                    if len(texts) > 2 and texts[2]:
                        record["Booking_Date"] = texts[2]
                else:
                    # Parse text block
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if lines:
                        record["Full_Name"] = lines[0]

                if record.get("Full_Name") or record.get("Booking_Number"):
                    records.append(record)
            except Exception:
                continue

        # Try to find and click "Next" button
        try:
            next_btn = page.ele('tag:button@@text():Next', timeout=3) or \
                       page.ele('css:.mat-paginator-navigation-next', timeout=2)
            if next_btn and next_btn.attr('disabled') is None:
                next_btn.click()
                time.sleep(2)
            else:
                break
        except Exception:
            break

    return records


def _parse_html_fallback(html):
    """Parse raw HTML with BeautifulSoup as last resort."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        records = []

        # Look for any table with inmate data
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    texts = [c.get_text(strip=True) for c in cells]
                    record = {
                        "County": "Duval",
                        "State": "FL",
                        "Facility": "Duval County Jail",
                        "Full_Name": texts[0] if texts[0] else None,
                        "Booking_Number": texts[1] if len(texts) > 1 else None,
                        "Scrape_Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    if record["Full_Name"]:
                        records.append(record)
        return records
    except Exception:
        return []


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Duval County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_duval(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
