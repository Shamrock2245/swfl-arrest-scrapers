#!/usr/bin/env python3
"""
Palm Beach County Arrest Scraper — solver.py
Target: https://www3.pbso.org/blotter/index.cfm

Two-phase approach:
  Phase 1: Search by date → paginate through ALL results → collect booking links
  Phase 2: Visit each booking detail page → scrape full record
"""

import sys
import json
import time
import re
import platform
import os
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_text(text):
    """Clean and normalize whitespace."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def parse_name(full_name):
    """Parse 'LAST, FIRST MIDDLE' format into components."""
    first, middle, last = "", "", ""
    if not full_name:
        return first, middle, last
    if ',' in full_name:
        parts = full_name.split(',', 1)
        last = parts[0].strip()
        remainder = parts[1].strip()
        if ' ' in remainder:
            r_parts = remainder.split(' ', 1)
            first = r_parts[0].strip()
            middle = r_parts[1].strip()
        else:
            first = remainder
    else:
        last = full_name
    return first, middle, last


def parse_bond(text):
    """Extract total bond amount from text containing $X,XXX.XX patterns."""
    amounts = re.findall(r'\$([0-9,]+(?:\.\d{2})?)', text)
    total = 0.0
    for amt in amounts:
        try:
            total += float(amt.replace(',', ''))
        except ValueError:
            pass
    return total


def setup_browser():
    """Configure and launch DrissionPage browser using shared core config."""
    from core.browser import create_browser
    return create_browser({"headless": True})


# ---------------------------------------------------------------------------
# Phase 1 — Search & Paginate to collect all summary data from list view
# ---------------------------------------------------------------------------

def search_and_collect(page, target_date, max_pages=50):
    """
    Search for a single date and paginate through ALL results.
    Returns list of dicts with summary-level data + booking number links.

    The list view already gives us: Name, Facility, Arresting Agency,
    Jacket Number, Race, Gender, OBTS Number, Booking Date/Time,
    Release Date, Holds, Booking Number (link), Charges, Bond amounts.
    """
    sys.stderr.write(f"\n--- Searching for {target_date} ---\n")

    # Navigate to search form
    page.get('https://www3.pbso.org/blotter/index.cfm')
    time.sleep(2)

    # Handle hCaptcha if present
    try:
        if page.ele('tag:iframe[src*="hcaptcha.com"]'):
            sys.stderr.write("⚠️  hCaptcha detected. Waiting 30s for manual solve...\n")
            time.sleep(30)
    except:
        pass

    # Fill search form
    if not page.wait.ele_displayed('#start_date', timeout=10):
        sys.stderr.write("❌ Search form did not load.\n")
        return []

    # Set both start and end date to the same day for single-day search
    start_input = page.ele('#start_date')
    end_input = page.ele('#end_date')

    start_input.clear()
    start_input.input(target_date)

    if end_input:
        end_input.clear()
        end_input.input(target_date)

    # Submit
    submit_btn = page.ele('#process') or page.ele('css:input[type=submit]')
    if not submit_btn:
        sys.stderr.write("❌ Submit button not found.\n")
        return []

    sys.stderr.write(f"Submitting search for {target_date}...\n")
    submit_btn.click()
    time.sleep(5)

    # Collect records from all pages
    all_summaries = []
    current_page = 1

    while current_page <= max_pages:
        sys.stderr.write(f"📄 Scraping page {current_page}...\n")

        # Wait for results
        if not page.wait.ele_displayed('css:div[id^="allresults_"]', timeout=10):
            # Could be "No records found" or page didn't load
            page_text = page.text or ""
            if "0 matches" in page_text or "no results" in page_text.lower():
                sys.stderr.write(f"   No results for {target_date}.\n")
            else:
                sys.stderr.write(f"   Results container not found on page {current_page}.\n")
            break

        # Parse total count from "X matches retrieved" text
        if current_page == 1:
            try:
                match_text = page.ele('xpath://*[contains(text(), "matches retrieved")]')
                if match_text:
                    sys.stderr.write(f"   {clean_text(match_text.text)}\n")
            except:
                pass

        # Parse each result card
        results = page.eles('css:div[id^="allresults_"]')
        sys.stderr.write(f"   Found {len(results)} records on page {current_page}.\n")

        for row in results:
            try:
                summary = _parse_list_row(row, page.url)
                if summary and summary.get('Booking_Number'):
                    all_summaries.append(summary)
            except Exception as e:
                sys.stderr.write(f"   ⚠️ Error parsing row: {e}\n")
                continue

        # --- Pagination ---
        if not _click_next_page(page):
            sys.stderr.write(f"   ✅ End of results (scraped {current_page} page(s)).\n")
            break

        current_page += 1
        time.sleep(3)

    sys.stderr.write(f"📊 Collected {len(all_summaries)} records for {target_date}.\n")
    return all_summaries


def _parse_list_row(row, page_url):
    """Parse a single result card from the list view into a summary dict."""

    def get_val(label):
        """Extract value for a label like 'Name:', 'Race:', etc."""
        try:
            strong = row.ele(f'xpath:.//strong[contains(text(), "{label}")]')
            if strong:
                parent = strong.parent()
                text = parent.text
                # Remove the label text to get the value
                val = text.split(label, 1)[-1].strip()
                # Clean up any "Label2: value2" that got appended
                return clean_text(val)
        except:
            pass
        return ''

    full_name = get_val("Name:")
    race = get_val("Race:")
    sex = get_val("Gender:")
    facility = get_val("Facility:")
    agency = get_val("Arresting Agency:")
    jacket_num = get_val("Jacket Number:")
    obts_num = get_val("OBTS Number:")
    booking_dt_str = get_val("Booking Date/Time:")
    release_date_str = get_val("Release Date:")
    holds_str = get_val("Holds For Other Agencies:")

    # Booking Number — usually a link with onclick="loaddetail(...)"
    booking_num = ""
    detail_onclick = ""
    try:
        link_ele = row.ele('css:a[onclick*="loaddetail"]')
        if link_ele:
            booking_num = clean_text(link_ele.text)
            detail_onclick = link_ele.attr('onclick') or ""
        else:
            # Fallback: any link in booking number area
            link_ele = row.ele('xpath:.//a[contains(@href, "booking")]')
            if link_ele:
                booking_num = clean_text(link_ele.text)
    except:
        booking_num = get_val("Booking Number:")

    # Mugshot
    mug_url = ""
    try:
        img = row.ele('css:img')
        if img:
            src = img.attr('src') or ""
            if src and 'noimage' not in src.lower():
                if not src.startswith('http'):
                    src = f"https://www3.pbso.org{src}"
                mug_url = src
    except:
        pass

    # Parse name
    first_name, middle_name, last_name = parse_name(full_name)

    # Parse booking date/time
    booking_date, booking_time = "", ""
    if booking_dt_str:
        try:
            dt = datetime.strptime(booking_dt_str.strip(), '%m/%d/%Y %H:%M')
            booking_date = dt.strftime('%Y-%m-%d')
            booking_time = dt.strftime('%H:%M:00')
        except:
            booking_date = booking_dt_str.strip()

    # Status
    status = "In Custody"
    if release_date_str and "N/A" not in release_date_str and release_date_str.strip():
        status = "Released"

    # Charges & Bond from list view
    charges = []
    total_bond = 0.0
    try:
        inner_rows = row.eles('css:div.row')
        for ir in inner_rows:
            txt = ir.text.strip().replace('\n', ' ')
            # Skip non-charge rows (they have statute numbers like 843.15)
            if re.search(r'\d+\.\d+', txt) and "Booking" not in txt and "OBTS" not in txt:
                # Extract the charge description
                # Pattern: "statute_num degree (level) CHARGE_DESCRIPTION Original Bond: ... Current Bond: ..."
                charge_part = txt
                # Remove bond info
                for splitter in ["Original Bond", "Current Bond", "Bond Information"]:
                    if splitter in charge_part:
                        charge_part = charge_part.split(splitter)[0]

                charge_part = charge_part.strip()
                if charge_part:
                    charges.append(charge_part)

        # Bond amounts
        row_text = row.text or ""
        bond_matches = re.findall(r'Current Bond:\s*\$([0-9,]+(?:\.\d{2})?)', row_text)
        for amt in bond_matches:
            try:
                total_bond += float(amt.replace(',', ''))
            except:
                pass
    except:
        pass

    bond_amount_str = f"{total_bond:.2f}" if total_bond > 0 else "0"

    return {
        "Scrape_Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "County": "Palm Beach",
        "Booking_Number": booking_num,
        "Person_ID": jacket_num,
        "Full_Name": full_name,
        "First_Name": first_name,
        "Middle_Name": middle_name,
        "Last_Name": last_name,
        "DOB": "",
        "Arrest_Date": booking_date,
        "Arrest_Time": booking_time,
        "Booking_Date": booking_date,
        "Booking_Time": booking_time,
        "Status": status,
        "Facility": facility,
        "Agency": agency or "PBSO",
        "Race": race,
        "Sex": sex,
        "Height": "",
        "Weight": "",
        "Address": "",
        "City": "",
        "State": "",
        "ZIP": "",
        "Mugshot_URL": mug_url,
        "Charges": " | ".join(charges),
        "Bond_Amount": bond_amount_str,
        "Bond_Paid": "NO",
        "Bond_Type": "",
        "Court_Type": "",
        "Case_Number": "",
        "Court_Date": "",
        "Court_Time": "",
        "Court_Location": "",
        "Detail_URL": "",
        "Lead_Score": "0",
        "Lead_Status": "Cold",
        "LastChecked": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "LastCheckedMode": "scrape",
        # Internal: used for Phase 2 detail scraping
        "_detail_onclick": detail_onclick,
        "_obts": obts_num,
        "_holds": holds_str,
    }


def _click_next_page(page):
    """
    Click the '»' (next page) pagination link.
    Returns True if next page was found and clicked, False if at end.

    Pagination structure: Page 1 of 25 | 1 2 3 4 5 » Last »
    We want '»' (single right-arrow), NOT 'Last »'.
    """
    try:
        # Find all pagination links
        pagination_links = page.eles('xpath://a')
        for link in pagination_links:
            text = link.text.strip()
            # We want exactly '»' or '>' but NOT 'Last »' or 'Last >'
            if text in ('»', '>', '>>') and 'last' not in (link.text.lower()):
                link.click()
                return True

        # Fallback: look for numbered next page
        # Parse current page from "Page X of Y"
        try:
            page_info = page.ele('xpath://*[contains(text(), "Page ")]')
            if page_info:
                match = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', page_info.text)
                if match:
                    current = int(match.group(1))
                    total = int(match.group(2))
                    if current >= total:
                        return False
                    # Try clicking the next page number
                    next_num = str(current + 1)
                    next_link = page.ele(f'xpath://a[normalize-space(text())="{next_num}"]')
                    if next_link:
                        next_link.click()
                        return True
        except:
            pass

    except Exception as e:
        sys.stderr.write(f"   Pagination error: {e}\n")

    return False


# ---------------------------------------------------------------------------
# Phase 2 — Visit detail pages for extra fields (optional enhancement)
# ---------------------------------------------------------------------------

def enrich_with_detail(page, record):
    """
    Click into a booking detail page to get additional fields not on list view.
    Adds: DOB, Height, Weight, Address, City, State, ZIP, etc.
    
    The PBSO blotter uses loaddetail() JS to inject detail HTML into the page.
    This means we look for the #blotterdetails div content.
    """
    booking_num = record.get("Booking_Number", "")
    if not booking_num:
        return record

    try:
        # Click the booking number link
        link = page.ele(f'xpath://a[normalize-space(text())="{booking_num}"]')
        if not link:
            link = page.ele(f'css:a[onclick*="{booking_num}"]')
        if not link:
            return record

        link.click()
        time.sleep(2)

        # Wait for detail div to load
        detail_div = page.ele('css:#blotterdetails')
        if not detail_div:
            time.sleep(2)
            detail_div = page.ele('css:#blotterdetails')

        if not detail_div:
            # Try the whole page text as fallback
            detail_div = page

        detail_text = detail_div.text or ""

        # Extract fields from detail page
        def get_detail_val(label):
            pattern = rf'{label}\s*:?\s*(.+?)(?:\n|$)'
            m = re.search(pattern, detail_text, re.IGNORECASE)
            if m:
                return clean_text(m.group(1))
            return ""

        # DOB
        dob = get_detail_val("Date of Birth|DOB")
        if dob:
            record["DOB"] = dob

        # Height
        height = get_detail_val("Height")
        if height:
            record["Height"] = height

        # Weight
        weight = get_detail_val("Weight")
        if weight:
            record["Weight"] = weight

        # Address fields
        address = get_detail_val("Address|Street")
        if address:
            record["Address"] = address

        city = get_detail_val("City")
        if city:
            record["City"] = city

        state = get_detail_val("State")
        if state and len(state) <= 2:
            record["State"] = state

        zipcode = get_detail_val("Zip|ZIP")
        if zipcode:
            record["ZIP"] = zipcode

        # Set Detail URL
        record["Detail_URL"] = page.url

        # Go back to results list
        page.back()
        time.sleep(2)

    except Exception as e:
        sys.stderr.write(f"   ⚠️ Detail page error for {booking_num}: {e}\n")
        # Try to go back
        try:
            page.back()
            time.sleep(2)
        except:
            pass

    return record


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def scrape_palm_beach(days_back=1, max_pages=50):
    """
    Main scraper function.
    
    Args:
        days_back: Number of days to search (default 1 = today only)
        max_pages: Max pagination pages per date search
    
    Returns:
        List of record dicts matching the 39-column schema.
    """
    sys.stderr.write(f"🌴 Palm Beach County Scraper (PBSO Blotter)\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    page = setup_browser()
    all_records = []

    try:
        # Loop oldest → newest
        for i in range(days_back - 1, -1, -1):
            target_date_obj = datetime.now() - timedelta(days=i)
            target_date = target_date_obj.strftime('%m/%d/%Y')

            # Phase 1: Search & collect from list view
            summaries = search_and_collect(page, target_date, max_pages)

            if not summaries:
                continue

            # Phase 2: Optionally visit detail pages for enrichment
            # (PBSO detail pages may use AJAX injection — loaddetail())
            # We attempt it but don't fail if it doesn't work
            for idx, record in enumerate(summaries, 1):
                sys.stderr.write(
                    f"   🔍 [{idx}/{len(summaries)}] {record.get('Booking_Number', '?')} "
                    f"- {record.get('Full_Name', 'Unknown')}\n"
                )
                try:
                    enrich_with_detail(page, record)
                except Exception as e:
                    sys.stderr.write(f"   ⚠️ Enrichment failed: {e}\n")

                # Clean up internal fields before output
                record.pop('_detail_onclick', None)
                record.pop('_obts', None)
                record.pop('_holds', None)

            all_records.extend(summaries)

        sys.stderr.write(f"\n📊 Grand total: {len(all_records)} records across {days_back} day(s).\n")
        return all_records

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
        return all_records  # Return whatever we got

    finally:
        try:
            page.quit()
        except:
            pass


if __name__ == "__main__":
    days = 1
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass

    results = scrape_palm_beach(days_back=days)
    print(json.dumps(results, indent=2))
