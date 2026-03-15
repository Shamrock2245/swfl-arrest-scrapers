#!/usr/bin/env python3
"""
Brevard County Arrest Scraper
Target: https://inmatesearch.brevardsheriff.org/
Stack: Python (requests + BeautifulSoup)
Status: 🟢 Active

Approach: POST form with date range fields → results table → detail pages.
The search form at /Results accepts FromDate/ToDate, returns HTML table of bookings.
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


BASE_URL = "https://inmatesearch.brevardsheriff.org"
SEARCH_URL = f"{BASE_URL}/Results"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE_URL,
}


def scrape_brevard(days_back=7, max_pages=20):
    """
    Scrape Brevard County booking records.

    Args:
        days_back: Number of days to look back
        max_pages: Maximum number of result pages to process

    Returns:
        List of record dicts
    """
    sys.stderr.write(f"🐊 Brevard County Scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    # Load search page first to get any CSRF tokens
    try:
        home = session.get(BASE_URL, timeout=30)
        home.raise_for_status()
    except Exception as e:
        sys.stderr.write(f"❌ Failed to load search page: {e}\n")
        return []

    # Calculate date range
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)

    form_data = {
        "SearchForm.FromDate": from_date.strftime("%Y-%m-%d"),
        "SearchForm.ToDate": to_date.strftime("%Y-%m-%d"),
        "SearchForm.LastName": "",
        "SearchForm.FirstName": "",
        "SearchForm.SubjectNumber": "",
        "SearchForm.BookingNumber": "",
    }

    sys.stderr.write(f"📡 Searching {from_date.strftime('%m/%d/%Y')} → {to_date.strftime('%m/%d/%Y')}\n")

    records = []
    page_num = 1

    while page_num <= max_pages:
        try:
            if page_num == 1:
                resp = session.post(SEARCH_URL, data=form_data, timeout=30)
            else:
                # Pagination — check for page links
                resp = session.get(f"{SEARCH_URL}?page={page_num}", timeout=30)

            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Find result rows — look for table or card-based layout
            rows = soup.select("table tbody tr, .booking-row, .inmate-row, .result-row")

            if not rows:
                # Try finding links to detail pages
                detail_links = soup.select("a[href*='/Details/'], a[href*='/Booking/'], a[href*='booking']")
                if not detail_links and page_num == 1:
                    # Maybe results are in a different format
                    sys.stderr.write(f"⚠️  No result rows found on page {page_num}\n")
                    # Try to extract directly from the page
                    detail_links = soup.find_all("a", href=re.compile(r"/Details/|/Booking/|booking", re.IGNORECASE))

                if detail_links:
                    sys.stderr.write(f"📋 Found {len(detail_links)} booking links on page {page_num}\n")
                    for link in detail_links:
                        href = link.get("href", "")
                        if not href.startswith("http"):
                            href = BASE_URL + href
                        detail_record = _fetch_detail(session, href)
                        if detail_record:
                            records.append(detail_record)
                            time.sleep(0.5)  # Be polite
                else:
                    if page_num > 1:
                        sys.stderr.write(f"🏁 No more results on page {page_num}\n")
                    break
            else:
                sys.stderr.write(f"📋 Found {len(rows)} rows on page {page_num}\n")
                for row in rows:
                    record = _parse_row(row, session)
                    if record:
                        records.append(record)

            # Check for next page
            next_link = soup.select_one("a[href*='page='], .pagination .next a, a:contains('Next')")
            if not next_link:
                sys.stderr.write(f"🏁 No more pages after page {page_num}\n")
                break

            page_num += 1
            time.sleep(1)  # Rate limit

        except Exception as e:
            sys.stderr.write(f"❌ Error on page {page_num}: {e}\n")
            break

    sys.stderr.write(f"📊 Total records: {len(records)}\n")
    return records


def _parse_row(row, session):
    """Parse a table row or card element into a record dict."""
    try:
        cells = row.find_all("td")
        if len(cells) < 2:
            return None

        # Try to find a detail link
        link = row.find("a", href=True)
        detail_url = None
        if link:
            href = link.get("href", "")
            if not href.startswith("http"):
                href = BASE_URL + href
            detail_url = href

        record = {
            "County": "Brevard",
            "State": "FL",
            "Facility": "Brevard County Jail",
        }

        # Extract text from cells — adapt based on actual column layout
        texts = [c.get_text(strip=True) for c in cells]

        if len(texts) >= 1:
            record["Full_Name"] = texts[0]
        if len(texts) >= 2:
            record["Booking_Number"] = texts[1]
        if len(texts) >= 3:
            record["Booking_Date"] = texts[2]
        if len(texts) >= 4:
            record["Charges"] = texts[3]

        # If we have a detail URL, fetch more info
        if detail_url:
            detail = _fetch_detail(session, detail_url)
            if detail:
                record.update(detail)

        if record.get("Full_Name") or record.get("Booking_Number"):
            return record
    except Exception as e:
        sys.stderr.write(f"   ⚠️  Row parse error: {e}\n")
    return None


def _fetch_detail(session, url):
    """Fetch booking detail page and extract fields."""
    try:
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        record = {
            "Detail_URL": url,
            "County": "Brevard",
            "State": "FL",
            "Facility": "Brevard County Jail",
        }

        # Extract data from label:value pairs
        def get_field(labels):
            """Try multiple label texts to find a value."""
            for label_text in labels:
                # Method 1: Find label element, get adjacent text
                label_el = soup.find(string=re.compile(label_text, re.IGNORECASE))
                if label_el:
                    parent = label_el.parent
                    if parent:
                        # Check next sibling or parent's text
                        next_el = parent.find_next_sibling()
                        if next_el:
                            val = next_el.get_text(strip=True)
                            if val:
                                return val
                        # Try same parent's text after the label
                        full = parent.get_text(strip=True)
                        parts = full.split(label_text, 1)
                        if len(parts) > 1:
                            val = parts[1].strip().lstrip(":").strip()
                            if val:
                                return val

                # Method 2: Table cells
                for td in soup.find_all("td"):
                    if label_text.lower() in td.get_text(strip=True).lower():
                        next_td = td.find_next_sibling("td")
                        if next_td:
                            return next_td.get_text(strip=True)
            return None

        record["Full_Name"] = get_field(["Name", "Inmate Name", "Full Name", "Subject Name"])
        record["Booking_Number"] = get_field(["Booking Number", "Booking #", "Booking No"])
        record["Booking_Date"] = get_field(["Booking Date", "Book Date", "Arrest Date"])
        record["DOB"] = get_field(["Date of Birth", "DOB", "Birth Date"])
        record["Sex"] = get_field(["Gender", "Sex"])
        record["Race"] = get_field(["Race", "Ethnicity"])
        record["Address"] = get_field(["Address", "Home Address"])

        # Parse name into first/last if possible
        name = record.get("Full_Name", "")
        if name and "," in name:
            parts = name.split(",", 1)
            record["Last_Name"] = parts[0].strip()
            record["First_Name"] = parts[1].strip()

        # Extract charges
        charges = []
        charge_elements = soup.find_all(string=re.compile(r"charge|offense", re.IGNORECASE))
        charge_rows = soup.select("table.charges tr, .charge-row, [class*='charge']")
        for cr in charge_rows:
            charge_text = cr.get_text(strip=True)
            if charge_text and len(charge_text) > 3:
                charges.append(charge_text)
        if charges:
            record["Charges"] = " | ".join(charges)

        # Extract bond amount
        bond = get_field(["Bond Amount", "Bond", "Total Bond", "Bond Total"])
        if bond:
            # Clean bond amount
            cleaned = re.sub(r'[^\d.]', '', bond)
            record["Bond_Amount"] = cleaned

        # Extract mugshot
        mugshot = soup.find("img", src=re.compile(r"photo|mugshot|inmate", re.IGNORECASE))
        if mugshot and mugshot.get("src"):
            src = mugshot["src"]
            if not src.startswith("http"):
                src = BASE_URL + src
            record["Mugshot_URL"] = src

        # Clean None values
        record = {k: v for k, v in record.items() if v is not None}

        if record.get("Full_Name") or record.get("Booking_Number"):
            sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')} ({record.get('Booking_Number', 'N/A')})\n")
            return record

    except Exception as e:
        sys.stderr.write(f"   ⚠️  Detail page error: {e}\n")
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Brevard County Arrest Scraper")
    parser.add_argument("--days-back", type=int, default=7)
    parser.add_argument("--max-pages", type=int, default=20)
    args = parser.parse_args()

    records = scrape_brevard(args.days_back, args.max_pages)
    print(json.dumps(records, default=str))
