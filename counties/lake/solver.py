#!/usr/bin/env python3
"""
Lake County Arrest Scraper
Target: https://www.lcso.org/inmates/
Stack: Python (DrissionPage)
Status: 🟢 Active

Approach: The site is JS-rendered (Angular template markers visible).
Use DrissionPage to interact with the search form and extract results.
"""

import sys
import json
import time
import re
from datetime import datetime

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')


BASE_URL = "https://www.lcso.org"
SEARCH_URL = f"{BASE_URL}/inmates/"


def scrape_lake(days_back=7, max_pages=10):
    """
    Scrape Lake County booking records using DrissionPage.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum result pages to process

    Returns:
        List of record dicts
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    sys.stderr.write(f"🐊 Lake County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    # Configure browser
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

    try:
        sys.stderr.write(f"📡 Loading: {SEARCH_URL}\n")
        page.get(SEARCH_URL)
        time.sleep(5)  # Wait for JS rendering

        # Handle CloudFlare if present
        for attempt in range(10):
            title = page.title or ''
            if 'just a moment' in title.lower() or 'security' in title.lower():
                sys.stderr.write(f"⏳ [{attempt+1}/10] Waiting for Cloudflare...\n")
                time.sleep(3)
            else:
                sys.stderr.write(f"✅ Page loaded: {title}\n")
                break

        # Try to find and interact with search form
        # Lake County uses an Angular-based search
        try:
            # Look for search input or button
            search_btn = page.ele('text:Search', timeout=5)
            if search_btn:
                search_btn.click()
                time.sleep(3)
                sys.stderr.write("   👆 Clicked Search\n")
        except Exception:
            sys.stderr.write("   ℹ️  No search button found, checking for direct results\n")

        # Try to find result rows/links
        page_num = 0
        while page_num < max_pages:
            page_num += 1
            sys.stderr.write(f"📄 Processing page {page_num}...\n")

            # Look for inmate cards/rows/links
            inmate_links = page.eles('xpath://a[contains(@href, "inmate") or contains(@href, "booking") or contains(@href, "details")]')

            if not inmate_links:
                # Try table rows
                inmate_links = page.eles('xpath://table//tr[td]')

            if not inmate_links:
                # Try any content that looks like inmate data
                cards = page.eles('xpath://div[contains(@class, "inmate") or contains(@class, "result") or contains(@class, "card")]')
                if cards:
                    sys.stderr.write(f"   Found {len(cards)} result cards\n")
                    for card in cards:
                        record = _parse_card(card)
                        if record:
                            records.append(record)
                elif page_num == 1:
                    sys.stderr.write("   ⚠️  No results found on page\n")
                break
            else:
                sys.stderr.write(f"   Found {len(inmate_links)} inmate entries\n")
                for link in inmate_links:
                    try:
                        record = _parse_element(link, page)
                        if record:
                            records.append(record)
                    except Exception as e:
                        sys.stderr.write(f"   ⚠️  Parse error: {e}\n")

            # Try pagination
            try:
                next_btn = page.ele('text:Next', timeout=3) or page.ele('xpath://a[contains(@class, "next")]', timeout=2)
                if next_btn:
                    next_btn.click()
                    time.sleep(2)
                else:
                    break
            except Exception:
                break

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
    finally:
        try:
            page.quit()
        except Exception:
            pass

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _parse_element(element, page):
    """Parse an inmate element (link, row, or card) into a record."""
    try:
        record = {
            "County": "Lake",
            "State": "FL",
            "Facility": "Lake County Jail",
        }

        text = element.text or ""

        # Try to extract name
        name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+)', text)
        if name_match:
            record["Full_Name"] = name_match.group(1)
            parts = record["Full_Name"].split(",", 1)
            record["Last_Name"] = parts[0].strip()
            record["First_Name"] = parts[1].strip() if len(parts) > 1 else ""

        # Try to get booking number
        booking_match = re.search(r'(?:Booking|BK|Book)[\s#:]*(\d{4,}[-]?\d*)', text, re.IGNORECASE)
        if booking_match:
            record["Booking_Number"] = booking_match.group(1)

        # Try to get DOB
        dob_match = re.search(r'(?:DOB|Birth)[\s:]*(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if dob_match:
            record["DOB"] = dob_match.group(1)

        # Try to get bond
        bond_match = re.search(r'(?:Bond|Bail)[\s:$]*(\$?[\d,]+\.?\d*)', text, re.IGNORECASE)
        if bond_match:
            record["Bond_Amount"] = re.sub(r'[^\d.]', '', bond_match.group(1))

        # Check for a detail URL
        href = element.attr("href") if hasattr(element, 'attr') else None
        if href:
            if not href.startswith("http"):
                href = BASE_URL + href
            record["Detail_URL"] = href

        # Clean None values
        record = {k: v for k, v in record.items() if v}

        if record.get("Full_Name") or record.get("Booking_Number"):
            sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")
            return record
    except Exception as e:
        sys.stderr.write(f"   ⚠️  Element parse error: {e}\n")
    return None


def _parse_card(card):
    """Parse a card-style inmate display."""
    return _parse_element(card, None)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lake County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    records = scrape_lake(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
