#!/usr/bin/env python3
"""
Highlands County Arrest Scraper
Target: https://www.highlandssheriff.org/inmateSearch
Stack: Python (DrissionPage)
Status: 🟢 Active

Approach: The site is a React SPA behind Cloudflare. Uses a myocv.com CMS.
DrissionPage required to handle Cloudflare challenge and render React content.
"""

import sys
import json
import time
import re
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "https://www.highlandssheriff.org"
SEARCH_URL = f"{BASE_URL}/inmateSearch"


def scrape_highlands(days_back=7, max_pages=10):
    """
    Scrape Highlands County booking records using DrissionPage.

    The site is a React SPA served via myocv.com CDN, behind Cloudflare.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum result pages

    Returns:
        List of record dicts
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    sys.stderr.write(f"🐊 Highlands County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    options = ChromiumOptions()
    options.headless()
    options.set_argument('--no-sandbox')
    options.set_argument('--disable-dev-shm-usage')
    options.set_argument('--disable-blink-features=AutomationControlled')
    options.set_argument('--window-size=1920,1080')
    options.set_user_agent(
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    )

    page = ChromiumPage(options)
    records = []
    api_responses = []

    try:
        # Set up network interception to catch API calls
        page.listen.start('json')

        sys.stderr.write(f"📡 Loading: {SEARCH_URL}\n")
        page.get(SEARCH_URL)

        # Wait for Cloudflare
        for attempt in range(15):
            title = page.title or ''
            if 'just a moment' in title.lower() or 'security' in title.lower() or 'checking' in title.lower():
                sys.stderr.write(f"⏳ [{attempt+1}/15] Waiting for Cloudflare...\n")
                time.sleep(3)
            else:
                sys.stderr.write(f"✅ Page loaded: {title}\n")
                break

        time.sleep(5)  # Extra wait for React hydration

        # Check for intercepted API responses (React apps often fetch data via API)
        packets = page.listen.steps(timeout=10)
        for packet in packets:
            try:
                if hasattr(packet, 'response') and packet.response:
                    body = packet.response.body
                    if isinstance(body, (dict, list)):
                        api_responses.append(body)
                    elif isinstance(body, str) and body.startswith('{'):
                        api_responses.append(json.loads(body))
            except Exception:
                pass

        if api_responses:
            sys.stderr.write(f"📡 Intercepted {len(api_responses)} API responses\n")
            for data in api_responses:
                _extract_from_api(data, records)

        # Also try to parse the rendered DOM
        if not records:
            sys.stderr.write("📜 Trying DOM extraction...\n")
            time.sleep(3)

            # Look for inmate cards/rows in the rendered React content
            all_cards = page.eles('xpath://div[contains(@class, "card") or contains(@class, "inmate") or contains(@class, "result")]')
            if all_cards:
                sys.stderr.write(f"   Found {len(all_cards)} result cards\n")
                for card in all_cards:
                    record = _parse_dom_element(card)
                    if record:
                        records.append(record)

            # Try table-based layout
            if not records:
                rows = page.eles('xpath://table//tr[td]')
                if rows:
                    sys.stderr.write(f"   Found {len(rows)} table rows\n")
                    for row in rows:
                        record = _parse_dom_element(row)
                        if record:
                            records.append(record)

            # Last resort: regex name extraction from page text
            if not records:
                body_text = page.ele('tag:body').text if page.ele('tag:body') else ''
                if body_text:
                    name_matches = re.findall(
                        r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+(?:\s[A-Z]\.?)?)',
                        body_text
                    )
                    sys.stderr.write(f"   Regex found {len(name_matches)} potential names in DOM text\n")
                    for name in name_matches[:50]:
                        # Skip common non-name strings
                        if any(skip in name.lower() for skip in ['county', 'sheriff', 'office', 'search', 'inmate']):
                            continue
                        records.append({
                            "Full_Name": name,
                            "County": "Highlands",
                            "State": "FL",
                            "Facility": "Highlands County Jail",
                        })

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
    finally:
        try:
            page.listen.stop()
            page.quit()
        except Exception:
            pass

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _extract_from_api(data, records):
    """Extract records from intercepted API JSON response."""
    try:
        # Handle different API response shapes
        entries = []
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict):
            # Common keys for paginated results
            for key in ['entries', 'data', 'results', 'items', 'inmates', 'records']:
                if key in data and isinstance(data[key], list):
                    entries = data[key]
                    break

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            record = {
                "County": "Highlands",
                "State": "FL",
                "Facility": "Highlands County Jail",
            }

            # Try common field names
            for name_key in ['name', 'full_name', 'fullName', 'title', 'inmateName', 'defendant_name']:
                if name_key in entry:
                    record["Full_Name"] = str(entry[name_key]).strip()
                    break

            for bk_key in ['booking_number', 'bookingNumber', 'id', 'inmateId', 'booking_id']:
                if bk_key in entry:
                    record["Booking_Number"] = str(entry[bk_key]).strip()
                    break

            for dob_key in ['dob', 'dateOfBirth', 'date_of_birth', 'DOB']:
                if dob_key in entry:
                    record["DOB"] = str(entry[dob_key]).strip()
                    break

            for bond_key in ['bond', 'bondAmount', 'bond_amount', 'totalBond']:
                if bond_key in entry:
                    record["Bond_Amount"] = str(entry[bond_key]).strip()
                    break

            for charge_key in ['charges', 'charge', 'offense', 'offenses']:
                val = entry.get(charge_key)
                if val:
                    if isinstance(val, list):
                        record["Charges"] = " | ".join(str(c) for c in val)
                    else:
                        record["Charges"] = str(val)
                    break

            # Parse HTML content if present (like Hendry pattern)
            if 'content' in entry and isinstance(entry['content'], str):
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(entry['content'], 'html.parser')
                text = soup.get_text()

                if not record.get("Full_Name"):
                    name_match = re.search(r'([A-Z][a-z]+,\s*[A-Z][a-z]+)', text)
                    if name_match:
                        record["Full_Name"] = name_match.group(1)

            # Parse name
            name = record.get("Full_Name", "")
            if name and "," in name:
                parts = name.split(",", 1)
                record["Last_Name"] = parts[0].strip()
                record["First_Name"] = parts[1].strip()

            record = {k: v for k, v in record.items() if v}
            if record.get("Full_Name") or record.get("Booking_Number"):
                records.append(record)
                sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")

    except Exception as e:
        sys.stderr.write(f"   ⚠️  API extraction error: {e}\n")


def _parse_dom_element(element):
    """Parse a rendered DOM element into a record dict."""
    try:
        record = {
            "County": "Highlands",
            "State": "FL",
            "Facility": "Highlands County Jail",
        }

        text = element.text or ""

        name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+)', text)
        if name_match:
            record["Full_Name"] = name_match.group(1)
            parts = record["Full_Name"].split(",", 1)
            record["Last_Name"] = parts[0].strip()
            record["First_Name"] = parts[1].strip() if len(parts) > 1 else ""

        booking_match = re.search(r'(?:Booking|BK)[\s#:]*(\d{4,}[-]?\d*)', text, re.IGNORECASE)
        if booking_match:
            record["Booking_Number"] = booking_match.group(1)

        dob_match = re.search(r'(?:DOB|Birth)[\s:]*(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if dob_match:
            record["DOB"] = dob_match.group(1)

        bond_match = re.search(r'(?:Bond|Bail)[\s:$]*(\$?[\d,]+\.?\d*)', text, re.IGNORECASE)
        if bond_match:
            record["Bond_Amount"] = re.sub(r'[^\d.]', '', bond_match.group(1))

        record = {k: v for k, v in record.items() if v}
        if record.get("Full_Name") or record.get("Booking_Number"):
            sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")
            return record
    except Exception as e:
        sys.stderr.write(f"   ⚠️  DOM parse error: {e}\n")
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Highlands County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    records = scrape_highlands(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
