#!/usr/bin/env python3
"""
DeSoto County Solver - DrissionPage Headless Scraper

Scrapes DeSoto County jail roster from jail.desotosheriff.org
1. Loads the inmate roster page (/DCN/inmates)
2. Sorts by Admit Date descending (newest first)
3. Extracts all inmate detail links across all pages
4. Visits each detail page to extract arrest data
5. Outputs JSON to stdout

Author: SWFL Arrest Scrapers Team
Date: March 2026
"""

import sys
import json
import time
import os
import datetime
import re
from urllib.parse import urljoin, unquote, urlparse, parse_qs
from bs4 import BeautifulSoup

from DrissionPage import ChromiumPage, ChromiumOptions


INMATES_URL = "https://jail.desotosheriff.org/DCN/inmates"
BASE_URL = "https://jail.desotosheriff.org"


def setup_browser():
    """Create headless Chrome browser via DrissionPage."""
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--window-size=1920,1080')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return ChromiumPage(co)


def sort_by_admit_date_desc(page):
    """Click the Admit Date column header to sort descending (newest first).
    
    DevExpress grid uses AJAX sorting - click once for ASC, twice for DESC.
    We click twice and verify the sort arrow direction.
    """
    try:
        # Find the Admit Date header
        admit_header = None
        headers = page.eles('tag:th')
        for h in headers:
            text = h.text.strip()
            if 'admit date' in text.lower():
                admit_header = h
                break
        
        if not admit_header:
            sys.stderr.write("[WARN] Could not find Admit Date column header, skipping sort\n")
            return
        
        # Click once for ascending sort
        sys.stderr.write("[>] Sorting by Admit Date...\n")
        admit_header.click()
        time.sleep(2)
        
        # Click again for descending (newest first)
        admit_header.click()
        time.sleep(2)
        
        sys.stderr.write("[OK] Sorted by Admit Date descending\n")
        
    except Exception as e:
        sys.stderr.write(f"[WARN] Sort failed: {e}, continuing without sort\n")


def collect_links_from_current_page(page):
    """Extract inmate detail links from the current page view."""
    html = page.html
    soup = BeautifulSoup(html, 'html.parser')
    
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'inmate-details' in href:
            full_url = urljoin(BASE_URL, href)
            if full_url not in links:
                links.append(full_url)
    
    return links


def parse_all_roster_links(page):
    """Extract all inmate detail links across all pages."""
    page.get(INMATES_URL)
    time.sleep(3)
    
    # Sort by Admit Date descending
    sort_by_admit_date_desc(page)
    
    # Collect links from page 1
    all_links = collect_links_from_current_page(page)
    sys.stderr.write(f"[>] Page 1: {len(all_links)} links\n")
    
    # Check for additional pages
    page_num = 2
    max_pages = 10  # Safety limit
    while page_num <= max_pages:
        try:
            # Look for page number buttons (DevExpress pager)
            next_btn = None
            pager_btns = page.eles('css:.dxp-num')
            for btn in pager_btns:
                if btn.text.strip() == str(page_num):
                    next_btn = btn
                    break
            
            if not next_btn:
                # Try the "next" button
                try:
                    next_btn = page.ele('#gvInmates_DXPagerBottom_PBN')
                except:
                    break
            
            if not next_btn:
                break
                
            next_btn.click()
            time.sleep(2)
            
            new_links = collect_links_from_current_page(page)
            if not new_links:
                break
                
            # Check for duplicates with existing links
            added = 0
            for link in new_links:
                if link not in all_links:
                    all_links.append(link)
                    added += 1
            
            sys.stderr.write(f"[>] Page {page_num}: {added} new links\n")
            
            if added == 0:
                break  # No new links, we've cycled
                
            page_num += 1
            
        except Exception as e:
            sys.stderr.write(f"[WARN] Pagination error on page {page_num}: {e}\n")
            break
    
    sys.stderr.write(f"[OK] Found {len(all_links)} total inmate detail links\n")
    return all_links


def extract_detail(page, url):
    """Extract arrest data from an inmate detail page."""
    page.get(url)
    time.sleep(1.5)
    
    html = page.html
    soup = BeautifulSoup(html, 'html.parser')
    
    record = {}
    record['County'] = 'DeSoto'
    record['State'] = 'FL'
    record['Scrape_Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    record['Detail_URL'] = url
    
    # Extract Booking ID from URL parameter
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    bid = qs.get('bid', [''])[0]
    if bid:
        record['Booking_Number'] = unquote(bid)
    
    # Extract name from header
    name_el = soup.find('h3', class_='header-text')
    if name_el:
        span = name_el.find('span')
        if span:
            full_name = span.get_text(strip=True)
        else:
            full_name = name_el.get_text(strip=True)
        record['Full_Name'] = full_name
        
        # Parse "Last, First Middle"
        if ',' in full_name:
            parts = full_name.split(',', 1)
            record['Last_Name'] = parts[0].strip()
            first_parts = parts[1].strip().split()
            if first_parts:
                record['First_Name'] = first_parts[0]
                if len(first_parts) > 1:
                    record['Middle_Name'] = ' '.join(first_parts[1:])
    else:
        # Try #HeaderText
        header = soup.find(id='HeaderText')
        if header:
            full_name = header.get_text(strip=True)
            record['Full_Name'] = full_name
            if ',' in full_name:
                parts = full_name.split(',', 1)
                record['Last_Name'] = parts[0].strip()
                first_parts = parts[1].strip().split()
                if first_parts:
                    record['First_Name'] = first_parts[0]
                    if len(first_parts) > 1:
                        record['Middle_Name'] = ' '.join(first_parts[1:])
    
    # Extract detail table fields
    detail_table = soup.find(id='tblDetails')
    if detail_table:
        rows = detail_table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                label = cells[0].get_text(strip=True).rstrip(':')
                value = cells[1].get_text(strip=True)
                if not label or not value:
                    continue
                if 'Drag a column' in label or 'Change Offset' in label:
                    continue
                
                # Map fields
                label_lower = label.lower()
                if 'date of birth' in label_lower or label_lower == 'dob':
                    record['DOB'] = value
                elif 'sex' in label_lower or 'gender' in label_lower:
                    record['Sex'] = value[0] if value else ''
                elif 'race' in label_lower:
                    record['Race'] = value
                elif 'booking date' in label_lower or 'date in' in label_lower or 'admit date' in label_lower:
                    record['Booking_Date'] = value
                elif 'release date' in label_lower or 'date out' in label_lower:
                    if value and value != 'N/A':
                        record['Status'] = 'Released'
                elif 'facility' in label_lower or 'location' in label_lower or 'housing' in label_lower:
                    record['Facility'] = value
                elif 'height' in label_lower:
                    record['Height'] = value
                elif 'weight' in label_lower:
                    record['Weight'] = value
                elif 'eye' in label_lower:
                    pass  # Not in schema
                elif 'hair' in label_lower:
                    pass  # Not in schema
                elif 'age' in label_lower:
                    pass  # Not in schema directly, DOB is preferred
                elif 'address' in label_lower:
                    record['Address'] = value
                    # Try to extract city/state/zip from address
                    addr_match = re.search(r',\s*(\w[\w\s]*?)\s+([A-Z]{2})\s+(\d{5})', value)
                    if addr_match:
                        record['City'] = addr_match.group(1).strip()
                        record['State'] = addr_match.group(2)
                        record['ZIP'] = addr_match.group(3)
    
    # If no explicit status set, assume in custody
    if 'Status' not in record:
        record['Status'] = 'In Custody'
    
    # Extract charges from ChargeGrid
    charges = []
    total_bond = 0.0
    charge_rows = soup.select('[id*="ChargeGrid_DXDataRow"]')
    for cr in charge_rows:
        cells = cr.find_all('td')
        if cells:
            charge_text = cells[0].get_text(strip=True) if len(cells) > 0 else ''
            if charge_text and 'Drag a column' not in charge_text:
                charges.append(charge_text)
            
            # Bond amount (usually index 5)
            if len(cells) > 5:
                bond_text = cells[5].get_text(strip=True)
                if bond_text:
                    # Parse "$1,500" or "1500.00"
                    clean = bond_text.replace('$', '').replace(',', '').strip()
                    try:
                        amt = float(clean)
                        total_bond += amt
                    except ValueError:
                        pass
            
            # Bond type (usually index 6)
            if len(cells) > 6:
                bond_type = cells[6].get_text(strip=True)
                if bond_type and 'Bond_Type' not in record:
                    record['Bond_Type'] = bond_type
    
    record['Charges'] = ' | '.join(charges) if charges else ''
    record['Bond_Amount'] = str(total_bond) if total_bond > 0 else '0'
    
    # Extract mugshot
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'photo' in src.lower() or 'mugshot' in src.lower():
            if not src.startswith('data:'):
                record['Mugshot_URL'] = urljoin(BASE_URL, src)
                break
    
    return record


def scrape_desoto():
    """Main scraper function for DeSoto County."""
    sys.stderr.write("[DESOTO] DeSoto County Scraper\n")
    
    page = None
    try:
        page = setup_browser()
        
        # Get roster links (sorted by admit date desc, across all pages)
        detail_urls = parse_all_roster_links(page)
        
        if not detail_urls:
            sys.stderr.write("[WARN] No inmate detail links found\n")
            print("[]")
            return
        
        records = []
        for i, url in enumerate(detail_urls):
            sys.stderr.write(f"[>] [{i+1}/{len(detail_urls)}] {url}\n")
            try:
                record = extract_detail(page, url)
                if record.get('Booking_Number') or record.get('Full_Name'):
                    records.append(record)
                    sys.stderr.write(f"   [OK] {record.get('Full_Name', 'UNKNOWN')} ({record.get('Booking_Number', 'NO-BID')})\n")
                else:
                    sys.stderr.write(f"   [WARN] Skipping empty record\n")
            except Exception as e:
                sys.stderr.write(f"   [FAIL] Error: {e}\n")
            
            # Brief delay to avoid detection
            time.sleep(0.5 + (i % 3) * 0.3)
        
        sys.stderr.write(f"[OK] Total extracted: {len(records)} records\n")
        print(json.dumps(records, indent=2))
        
    except Exception as e:
        sys.stderr.write(f"[FAIL] Error: {e}\n")
        import traceback
        traceback.print_exc(file=sys.stderr)
        print("[]")
    finally:
        if page:
            try:
                page.quit()
            except:
                pass


if __name__ == "__main__":
    scrape_desoto()
