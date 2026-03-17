#!/usr/bin/env python3
"""
Hillsborough County Solver (HCSO) - Headless Login + Scrape

Uses DrissionPage in headless mode to:
1. Navigate to HCSO Arrest Inquiry login page
2. Login with HCSO_EMAIL / HCSO_PASSWORD
3. Perform search for recent arrests
4. Parse results across paginated table
5. Output JSON to stdout

Requires: HCSO_EMAIL, HCSO_PASSWORD env vars

Author: SWFL Arrest Scrapers Team
Date: March 2026
"""

import sys
import json
import time
import os
import datetime
from bs4 import BeautifulSoup

# DrissionPage import
from DrissionPage import ChromiumPage, ChromiumOptions


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


def login_hcso(page, email, password):
    """Log into the HCSO Arrest Inquiry portal (handles reCAPTCHA v2 checkbox)."""
    login_url = "https://webapps.hcso.tampa.fl.us/arrestinquiry/Account/Login"
    sys.stderr.write(f"🔑 Navigating to login page...\n")
    page.get(login_url)
    time.sleep(3)

    # Fill email
    email_field = page.ele('#Email', timeout=10)
    if not email_field:
        sys.stderr.write("❌ Could not find email field\n")
        return False
    email_field.clear()
    email_field.input(email)

    # Fill password
    pwd_field = page.ele('#Password', timeout=5)
    if not pwd_field:
        sys.stderr.write("❌ Could not find password field\n")
        return False
    pwd_field.clear()
    pwd_field.input(password)

    # Toggle "Remember me" checkbox
    remember_me = page.ele('#RememberMe', timeout=3)
    if remember_me:
        try:
            remember_me.click()
            sys.stderr.write("✅ Remember Me toggled\n")
        except Exception:
            sys.stderr.write("⚠️  Could not toggle Remember Me\n")

    # Handle reCAPTCHA v2 checkbox (inside iframe)
    sys.stderr.write("🤖 Looking for reCAPTCHA...\n")
    recaptcha_solved = False
    try:
        # reCAPTCHA lives inside an iframe — find it
        recaptcha_iframe = page.ele('tag:iframe@@title=reCAPTCHA', timeout=5)
        if not recaptcha_iframe:
            # Try alternate selectors
            recaptcha_iframe = page.ele('tag:iframe@@src:recaptcha', timeout=3)
        
        if recaptcha_iframe:
            sys.stderr.write("   Found reCAPTCHA iframe, clicking checkbox...\n")
            # Switch into the iframe and click the checkbox
            iframe_page = recaptcha_iframe.ele('tag:div@@class:recaptcha-checkbox-border', timeout=5)
            if iframe_page:
                iframe_page.click()
                sys.stderr.write("   Clicked reCAPTCHA checkbox\n")
                time.sleep(3)
                recaptcha_solved = True
            else:
                # Try clicking the span with recaptcha-checkbox role
                checkbox = recaptcha_iframe.ele('#recaptcha-anchor', timeout=3)
                if checkbox:
                    checkbox.click()
                    sys.stderr.write("   Clicked reCAPTCHA anchor\n")
                    time.sleep(3)
                    recaptcha_solved = True
                else:
                    sys.stderr.write("   ⚠️  Could not find checkbox inside iframe\n")
        else:
            sys.stderr.write("   No reCAPTCHA iframe found (may not be required)\n")
            recaptcha_solved = True  # No CAPTCHA = proceed
    except Exception as e:
        sys.stderr.write(f"   ⚠️  reCAPTCHA handling error: {e}\n")

    if not recaptcha_solved:
        sys.stderr.write("⚠️  reCAPTCHA may not be solved, attempting login anyway...\n")

    # Wait a moment for reCAPTCHA to process
    time.sleep(2)

    # Click login button
    login_btn = page.ele('tag:button@@text():Log in', timeout=5) or page.ele('tag:input@@type=submit', timeout=3)
    if login_btn:
        login_btn.click()
    else:
        # Try form submit
        pwd_field.input('\n')
    
    time.sleep(5)
    
    # Check if login succeeded
    page_html = page.html
    current_url = page.url
    sys.stderr.write(f"   Post-login URL: {current_url}\n")
    
    if 'Log out' in page_html or 'Welcome' in page_html or 'Search' in page_html:
        sys.stderr.write("✅ Login successful\n")
        return True
    elif 'Invalid' in page_html or 'incorrect' in page_html.lower():
        sys.stderr.write("❌ Invalid credentials (may be reCAPTCHA block)\n")
        # Dump page snippet for debugging
        sys.stderr.write(f"   Page title: {page.title}\n")
        return False
    else:
        sys.stderr.write(f"⚠️  Login status unclear. Current URL: {current_url}\n")
        # Try to proceed anyway
        return 'arrestinquiry' in current_url.lower()


def perform_search(page, days_back=3):
    """Perform the arrest search with date range."""
    search_url = "https://webapps.hcso.tampa.fl.us/arrestinquiry/Home/Search"
    sys.stderr.write(f"🔍 Navigating to search page...\n")
    page.get(search_url)
    time.sleep(3)

    # Calculate date range
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days_back)
    
    start_str = start_date.strftime("%m/%d/%Y")
    end_str = end_date.strftime("%m/%d/%Y")
    
    sys.stderr.write(f"📅 Search range: {start_str} to {end_str}\n")

    # Fill start date
    start_field = page.ele('#BeginDate', timeout=5) or page.ele('@@name=BeginDate', timeout=3)
    if start_field:
        start_field.clear()
        start_field.input(start_str)

    # Fill end date
    end_field = page.ele('#EndDate', timeout=5) or page.ele('@@name=EndDate', timeout=3)
    if end_field:
        end_field.clear()
        end_field.input(end_str)

    # Click search button
    search_btn = page.ele('tag:button@@text():Search', timeout=5) or page.ele('#searchButton', timeout=3) or page.ele('tag:input@@value=Search', timeout=3)
    if search_btn:
        search_btn.click()
    else:
        sys.stderr.write("⚠️  Could not find search button, trying form submit...\n")
        if end_field:
            end_field.input('\n')
    
    time.sleep(5)
    
    # Check for results
    page_html = page.html
    if 'Search Results' in page_html or 'Booking Name' in page_html:
        sys.stderr.write("✅ Search results found\n")
        return True
    elif 'No records found' in page_html or 'no results' in page_html.lower():
        sys.stderr.write("⚠️  No records found for date range\n")
        return False
    else:
        sys.stderr.write(f"⚠️  Search result status unclear\n")
        return 'table-striped' in page_html


def parse_results_table(soup):
    """Parse arrest records from the BeautifulSoup object of a results page."""
    records = []
    
    # Find the main results table
    results_table = soup.find('table', class_='table-striped')
    if not results_table:
        return records
    
    # Find rows
    tbody = results_table.find('tbody') or results_table
    all_rows = tbody.find_all('tr', recursive=False)
    
    i = 0
    while i < len(all_rows):
        try:
            row = all_rows[i]
            cells = row.find_all('td', recursive=False)
            
            # Main row with name link (needs at least 5 cells)
            if len(cells) >= 5:
                name_cell = cells[0]
                name_link = name_cell.find('a')
                
                if name_link:
                    record = {}
                    record['County'] = 'Hillsborough'
                    record['Scrape_Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Name from link
                    full_name = name_link.get_text(strip=True)
                    record['Full_Name'] = full_name
                    if ',' in full_name:
                        parts = full_name.split(',', 1)
                        record['Last_Name'] = parts[0].strip()
                        first_parts = parts[1].strip().split()
                        if first_parts:
                            record['First_Name'] = first_parts[0]
                            if len(first_parts) > 1:
                                record['Middle_Name'] = ' '.join(first_parts[1:])
                    
                    # Detail URL
                    href = name_link.get('href', '')
                    if href:
                        if not href.startswith('http'):
                            href = 'https://webapps.hcso.tampa.fl.us' + href
                        record['Detail_URL'] = href
                    
                    # Booking #
                    record['Booking_Number'] = cells[1].get_text(strip=True)
                    
                    # Demographics: R / S / E / DOB
                    demo = cells[4].get_text(strip=True)
                    demo_parts = [p.strip() for p in demo.split('/')]
                    if len(demo_parts) >= 1:
                        record['Race'] = demo_parts[0]
                    if len(demo_parts) >= 2:
                        record['Sex'] = demo_parts[1]
                    if len(demo_parts) >= 4:
                        record['DOB'] = demo_parts[3]
                    
                    # Address row
                    if i + 1 < len(all_rows):
                        addr_row = all_rows[i + 1]
                        addr_cells = addr_row.find_all('td')
                        for cell in addr_cells:
                            text = cell.get_text(strip=True)
                            if text.startswith('ADDRESS:'):
                                record['Address'] = text.replace('ADDRESS:', '').strip()
                            elif text.startswith('CITY:'):
                                record['City'] = text.replace('CITY:', '').strip()
                    
                    # Release date row
                    if i + 2 < len(all_rows):
                        rel_row = all_rows[i + 2]
                        rel_cells = rel_row.find_all('td')
                        for cell in rel_cells:
                            text = cell.get_text(strip=True)
                            if text.startswith('ARREST DATE:'):
                                record['Arrest_Date'] = text.replace('ARREST DATE:', '').strip()
                            elif text.startswith('BOOKING DATE:'):
                                record['Booking_Date'] = text.replace('BOOKING DATE:', '').strip()
                            elif text.startswith('RELEASE DATE:'):
                                release_date = text.replace('RELEASE DATE:', '').strip()
                                if release_date:
                                    record['Status'] = 'Released'
                                else:
                                    record['Status'] = 'In Custody'
                            elif text.startswith('RELEASE CODE:'):
                                code = text.replace('RELEASE CODE:', '').strip()
                                record['Bond_Type'] = code
                    
                    # Charges in nested table
                    charges = []
                    case_numbers = []
                    total_bond = 0.0
                    if i + 3 < len(all_rows):
                        charge_row = all_rows[i + 3]
                        nested_table = charge_row.find('table')
                        if nested_table:
                            charge_rows = nested_table.find_all('tr')
                            for cr in charge_rows:
                                charge_cells = cr.find_all('td')
                                if len(charge_cells) >= 2:
                                    charge_desc = charge_cells[1].get_text(strip=True)
                                    if charge_desc and 'Charge Type' not in charge_desc:
                                        charges.append(charge_desc)
                                    
                                    # Bond Amount (Index 4)
                                    if len(charge_cells) >= 5:
                                        bond_text = charge_cells[4].get_text(strip=True)
                                        if '$' in bond_text or bond_text.replace(',','').replace('.','').isdigit():
                                            try:
                                                amt = float(bond_text.replace('$', '').replace(',', ''))
                                                total_bond += amt
                                            except:
                                                pass
                                    
                                    if len(charge_cells) >= 4:
                                        case_num = charge_cells[3].get_text(strip=True)
                                        if case_num and '-' in case_num and case_num not in case_numbers:
                                            case_numbers.append(case_num)
                    
                    record['Charges'] = ' | '.join(charges) if charges else ''
                    record['Bond_Amount'] = str(total_bond) if total_bond > 0 else '0'
                    
                    if case_numbers:
                        record['Case_Number'] = case_numbers[0]
                    
                    record['State'] = 'FL'
                    
                    # Only add records that have a booking number
                    if record.get('Booking_Number'):
                        records.append(record)
                    else:
                        sys.stderr.write(f"   ⚠️  Skipping record without booking number: {record.get('Full_Name', 'UNKNOWN')}\n")
                    
                    # Skip the related rows (4 rows per inmate)
                    i += 4
                    continue
            
            i += 1
            
        except Exception as e:
            sys.stderr.write(f"   ⚠️  Error parsing row {i}: {e}\n")
            i += 1
    
    return records


def scrape_hillsborough(days_back=3):
    """Main scraper function for Hillsborough County."""
    hcso_email = os.getenv('HCSO_EMAIL')
    hcso_password = os.getenv('HCSO_PASSWORD')
    
    if not hcso_email or not hcso_password:
        sys.stderr.write("❌ HCSO_EMAIL and HCSO_PASSWORD must be set\n")
        sys.stderr.write("   Hillsborough requires authorized member login.\n")
        print("[]")
        return
    
    sys.stderr.write(f"🏙️ Hillsborough County Scraper (days_back={days_back})\n")
    
    page = None
    try:
        page = setup_browser()
        
        # Step 1: Login
        if not login_hcso(page, hcso_email, hcso_password):
            sys.stderr.write("❌ Failed to login to HCSO\n")
            print("[]")
            return
        
        # Step 2: Search
        if not perform_search(page, days_back):
            sys.stderr.write("⚠️  No search results found\n")
            print("[]")
            return
        
        # Step 3: Parse results with pagination
        all_records = []
        current_page = 1
        max_pages = 20
        
        while current_page <= max_pages:
            sys.stderr.write(f"📄 Scraping page {current_page}...\n")
            
            page_html = page.html
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Pagination info
            pagination_info = soup.find('span', class_='paginationLeft')
            if pagination_info:
                sys.stderr.write(f"   {pagination_info.get_text(strip=True)}\n")
            
            # Parse records
            page_records = parse_results_table(soup)
            if not page_records:
                sys.stderr.write("   No records on this page\n")
                break
            
            all_records.extend(page_records)
            sys.stderr.write(f"   ✅ Parsed {len(page_records)} records (total: {len(all_records)})\n")
            
            # Check for Next button
            next_btn = page.ele('text:Next >', timeout=2)
            if next_btn:
                btn_class = next_btn.attr('class') or ''
                if 'disabled' in btn_class:
                    sys.stderr.write("   📄 Reached last page\n")
                    break
                next_btn.click()
                time.sleep(3)
                current_page += 1
            else:
                sys.stderr.write("   📄 No more pages\n")
                break
        
        sys.stderr.write(f"✅ Total extracted: {len(all_records)} records\n")
        
        # Output JSON to stdout
        print(json.dumps(all_records, indent=2))
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
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
    days = 3
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            pass
    scrape_hillsborough(days)
