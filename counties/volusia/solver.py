#!/usr/bin/env python3
"""
Volusia County Arrest Scraper
Target: https://www.volusia.org/services/public-protection/corrections/
Stack: Python (DrissionPage — TLS/anti-bot issues with raw requests)
Status: 🟢 Active

Approach: Volusia's site fails with TLS errors on raw requests.
We use DrissionPage to load the page, navigate to the inmate search,
and scrape the results table.
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


CORRECTIONS_URL = "https://www.volusia.org/services/public-protection/corrections/"
SEARCH_URL = "https://www.volusia.org/services/public-protection/corrections/inmate-information-search.stml"


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


def wait_for_cloudflare(page, max_wait=20):
    """Wait for any challenge page to clear."""
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ''
        if 'just a moment' not in title and 'checking' not in title:
            return True
        time.sleep(1)
        waited += 1
    return False


def scrape_volusia(days_back=7, max_pages=20):
    """
    Scrape Volusia County booking records.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum result pages

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Volusia County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    if not HAS_DRISSION:
        sys.stderr.write("❌ DrissionPage required for Volusia County\n")
        return []

    page = setup_browser()
    records = []

    try:
        # Step 1: Try the direct search URL first
        sys.stderr.write("📡 Loading Volusia corrections search...\n")
        page.get(SEARCH_URL)
        time.sleep(3)
        wait_for_cloudflare(page)

        current_url = page.url
        sys.stderr.write(f"📡 Landed on: {current_url}\n")
        sys.stderr.write(f"📡 Page title: {page.title}\n")

        # If the direct URL didn't work, try the corrections main page
        if 'error' in page.title.lower() or '404' in page.title or '404' in page.html[:200]:
            sys.stderr.write("⚠️  Direct search URL failed, trying corrections main page...\n")
            page.get(CORRECTIONS_URL)
            time.sleep(3)
            wait_for_cloudflare(page)

            # Look for "Inmate Information Search" link
            for link_text in ["Inmate Information Search", "Inmate Search", "Inmate Lookup", "Search Inmates"]:
                try:
                    link = page.ele(f'tag:a@@text():{link_text}', timeout=3)
                    if link:
                        sys.stderr.write(f"   Found link: {link_text}\n")
                        link.click()
                        time.sleep(3)
                        wait_for_cloudflare(page)
                        break
                except Exception:
                    continue

        # Step 2: Try to submit search form
        try:
            # Look for search inputs
            last_name_input = page.ele('tag:input@@name:LastName', timeout=3) or \
                              page.ele('tag:input@@name:lastname', timeout=2) or \
                              page.ele('tag:input@@id:LastName', timeout=2) or \
                              page.ele('tag:input@@placeholder:Last Name', timeout=2)

            # Submit empty search for all results
            search_btn = page.ele('tag:button@@text():Search', timeout=3) or \
                         page.ele('tag:input@@type=submit', timeout=2) or \
                         page.ele('tag:button@@type=submit', timeout=2) or \
                         page.ele('tag:input@@value=Search', timeout=2)

            if search_btn:
                sys.stderr.write("📡 Submitting search form...\n")
                search_btn.click()
                time.sleep(5)
            elif last_name_input:
                # Try entering a wildcard search
                last_name_input.clear()
                last_name_input.input('%')
                time.sleep(1)
                # Press Enter
                last_name_input.input('\n')
                time.sleep(5)
        except Exception as e:
            sys.stderr.write(f"   ⚠️  Search form interaction failed: {e}\n")

        # Step 3: Parse results
        sys.stderr.write("📡 Parsing results...\n")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page.html, "html.parser")

        # Find data tables
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2:
                continue

            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]

            # Check if this looks like an inmate table
            if not any(kw in " ".join(headers) for kw in ["name", "inmate", "booking", "charge", "arrest"]):
                continue

            sys.stderr.write(f"📋 Found data table: {len(rows) - 1} rows\n")
            sys.stderr.write(f"   Headers: {headers}\n")

            for row in rows[1:]:
                record = _parse_row(row, headers)
                if record:
                    records.append(record)
            break  # Only process first matching table

        # If no table, try to find list/card items
        if not records:
            items = soup.find_all("div", class_=re.compile(r"inmate|result|record|list-item|row", re.IGNORECASE))
            for item in items:
                record = _parse_card(item)
                if record:
                    records.append(record)

        # Pagination: try to find Next and keep going
        if records:
            for pg in range(1, max_pages):
                try:
                    next_btn = page.ele('tag:a@@text():Next', timeout=3) or \
                               page.ele('css:.next a', timeout=2) or \
                               page.ele('tag:a@@text():›', timeout=2)
                    if next_btn:
                        next_btn.click()
                        time.sleep(3)
                        soup = BeautifulSoup(page.html, "html.parser")
                        page_records = []
                        for table in soup.find_all("table"):
                            rows = table.find_all("tr")
                            if len(rows) < 2:
                                continue
                            headers = [th.get_text(strip=True).lower() for th in rows[0].find_all(["th", "td"])]
                            for row in rows[1:]:
                                record = _parse_row(row, headers)
                                if record:
                                    page_records.append(record)
                            break
                        if page_records:
                            sys.stderr.write(f"📋 Page {pg + 1}: {len(page_records)} records\n")
                            records.extend(page_records)
                        else:
                            break
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


def _parse_row(row, headers):
    """Parse a table row into a record dict."""
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    texts = [c.get_text(strip=True) for c in cells]

    record = {
        "County": "Volusia",
        "State": "FL",
        "Facility": "Volusia County Branch Jail",
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

    # Detail link
    link = row.find("a", href=True)
    if link:
        href = link["href"]
        if not href.startswith("http"):
            href = "https://www.volusia.org" + href
        record["Detail_URL"] = href

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


def _parse_card(card):
    """Parse a div/card element into a record."""
    text = card.get_text(" ", strip=True)
    if len(text) < 10:
        return None

    record = {
        "County": "Volusia",
        "State": "FL",
        "Facility": "Volusia County Branch Jail",
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

    if record.get("Full_Name") or record.get("Booking_Number"):
        return record
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Volusia County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_volusia(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
