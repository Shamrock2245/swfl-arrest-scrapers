#!/usr/bin/env python3
"""
Martin County Arrest Scraper
Target: https://www.martinso.us/inmatesearch/
Stack: Python (DrissionPage)
Status: 🟢 Active

Approach: Martin County uses martinso.us for their inmate search.
The original URL in the strategy CSV (mcsofl.org/224/Recent-Bookings) returned 404.
Using the official Martin County SO inmate search instead.
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

BASE_URL = "https://www.martinso.us"
SEARCH_URLS = [
    "https://www.martinso.us/inmatesearch/",
    "https://www.mcsofl.org/224/Recent-Bookings",
    "https://www.martinso.us/arrests/",
]


def scrape_martin(days_back=7, max_pages=10):
    """
    Scrape Martin County booking records using DrissionPage.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum pages to process

    Returns:
        List of record dicts
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    sys.stderr.write(f"🐊 Martin County Scraper\n")
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

    try:
        # Try each possible URL
        loaded = False
        for url in SEARCH_URLS:
            try:
                sys.stderr.write(f"📡 Trying: {url}\n")
                page.get(url)
                time.sleep(5)

                # Check for Cloudflare
                for attempt in range(10):
                    title = page.title or ''
                    if 'just a moment' in title.lower():
                        sys.stderr.write(f"⏳ [{attempt+1}/10] Waiting for Cloudflare...\n")
                        time.sleep(3)
                    else:
                        break

                # Check if page has content
                body_text = page.ele('tag:body').text if page.ele('tag:body') else ''
                if len(body_text) > 100 and '404' not in page.title:
                    sys.stderr.write(f"✅ Loaded: {page.title}\n")
                    loaded = True
                    break
            except Exception as e:
                sys.stderr.write(f"   ⚠️  Failed: {e}\n")

        if not loaded:
            sys.stderr.write("❌ Could not load any Martin County search URL\n")
            return []

        # Look for a disclaimer/accept button
        try:
            accept_btn = page.ele('text:Accept', timeout=3) or page.ele('text:I Agree', timeout=2)
            if accept_btn:
                accept_btn.click()
                time.sleep(2)
                sys.stderr.write("   👆 Accepted disclaimer\n")
        except Exception:
            pass

        # Try search form submission
        try:
            search_btn = page.ele('text:Search', timeout=3) or page.ele('xpath://input[@type="submit"]', timeout=2)
            if search_btn:
                search_btn.click()
                time.sleep(3)
                sys.stderr.write("   👆 Clicked Search\n")
        except Exception:
            pass

        # Parse results
        page_num = 0
        while page_num < max_pages:
            page_num += 1
            sys.stderr.write(f"📄 Processing page {page_num}...\n")

            # Try multiple selectors for results
            result_links = page.eles('xpath://a[contains(@href, "inmate") or contains(@href, "booking") or contains(@href, "detail")]')
            if not result_links:
                result_links = page.eles('xpath://table//tr[td]')

            if not result_links:
                # Try divs with inmate data patterns
                all_text = page.ele('tag:body').text if page.ele('tag:body') else ''
                name_pattern = re.findall(r'([A-Z][A-Z]+,\s*[A-Z][a-z]+(?:\s[A-Z]\.?)?)', all_text)
                if name_pattern:
                    sys.stderr.write(f"   Found {len(name_pattern)} name matches in page text\n")
                    for name in name_pattern[:50]:
                        records.append({
                            "Full_Name": name,
                            "County": "Martin",
                            "State": "FL",
                            "Facility": "Martin County Jail",
                        })
                else:
                    sys.stderr.write("   ⚠️  No results found\n")
                break

            sys.stderr.write(f"   Found {len(result_links)} entries\n")
            for link in result_links:
                record = _parse_element(link)
                if record:
                    records.append(record)

            # Pagination
            try:
                next_btn = page.ele('text:Next', timeout=3)
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


def _parse_element(element):
    """Parse an inmate element into a record dict."""
    try:
        record = {
            "County": "Martin",
            "State": "FL",
            "Facility": "Martin County Jail",
        }

        text = element.text or ""

        name_match = re.search(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)*,\s*[A-Z][a-z]+)', text)
        if name_match:
            record["Full_Name"] = name_match.group(1)
            parts = record["Full_Name"].split(",", 1)
            record["Last_Name"] = parts[0].strip()
            record["First_Name"] = parts[1].strip() if len(parts) > 1 else ""

        booking_match = re.search(r'(?:Booking|BK|Book)[\s#:]*(\d{4,}[-]?\d*)', text, re.IGNORECASE)
        if booking_match:
            record["Booking_Number"] = booking_match.group(1)

        dob_match = re.search(r'(?:DOB|Birth)[\s:]*(\d{1,2}/\d{1,2}/\d{4})', text, re.IGNORECASE)
        if dob_match:
            record["DOB"] = dob_match.group(1)

        bond_match = re.search(r'(?:Bond|Bail)[\s:$]*(\$?[\d,]+\.?\d*)', text, re.IGNORECASE)
        if bond_match:
            record["Bond_Amount"] = re.sub(r'[^\d.]', '', bond_match.group(1))

        href = element.attr("href") if hasattr(element, 'attr') else None
        if href:
            if not href.startswith("http"):
                href = BASE_URL + href
            record["Detail_URL"] = href

        record = {k: v for k, v in record.items() if v}

        if record.get("Full_Name") or record.get("Booking_Number"):
            sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")
            return record
    except Exception as e:
        sys.stderr.write(f"   ⚠️  Parse error: {e}\n")
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Martin County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=10)
    args = parser.parse_args()

    records = scrape_martin(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
