#!/usr/bin/env python3
"""
Osceola County Arrest Scraper
Source: https://apps.osceola.org/Apps/CorrectionsReports/Report/Daily/
System: Custom web application with date-based daily reports

This scraper navigates the Osceola County Corrections daily arrest report,
iterates through dates starting from a specified date, and extracts arrest
records including bond amounts from individual detail pages.

Known Limitations:
- Requires visiting each detail page to get bond amounts
- Date dropdown limited to ~30 days of history
- Some records may not have bond information
"""

import sys
import json
import re
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(str(text).strip().split())


def parse_date(date_str):
    """Parse various date formats to MM/DD/YYYY"""
    if not date_str:
        return ""
    
    # Try common formats
    formats = [
        '%m/%d/%Y',
        '%m/%d/%y',
        '%Y-%m-%d',
        '%b %d, %Y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%m/%d/%Y')
        except ValueError:
            continue
    
    return date_str


def parse_name(full_name):
    """Parse 'LAST, FIRST MIDDLE' format into components"""
    if not full_name:
        return "", "", ""
    
    full_name = clean_text(full_name)
    
    if ',' in full_name:
        parts = full_name.split(',', 1)
        last_name = parts[0].strip()
        first_middle = parts[1].strip() if len(parts) > 1 else ""
        
        # Split first and middle
        name_parts = first_middle.split()
        first_name = name_parts[0] if name_parts else ""
        
        return full_name, first_name, last_name
    
    return full_name, "", full_name


def extract_bond_amount(bond_str):
    """Extract numeric bond amount from string like '$2,000' or 'Total Bond: $2,000'"""
    if not bond_str:
        return ""
    
    # Find dollar amount pattern
    match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', str(bond_str))
    if match:
        # Remove commas and return numeric value
        return match.group(1).replace(',', '')
    
    return ""


def scrape_detail_page(page, inmate_id):
    """
    Scrape individual inmate detail page for bond and additional info.
    Returns dict with bond_amount, mugshot_url, charges_detail, etc.
    """
    detail_url = f"https://apps.osceola.org/Apps/CorrectionsReports/Report/Details/{inmate_id}"
    
    try:
        page.goto(detail_url, wait_until='networkidle', timeout=30000)
        time.sleep(1)
        
        result = {
            'bond_amount': '',
            'total_bond': '',
            'mugshot_url': '',
            'charges_detail': [],
            'race': '',
            'sex': '',
            'dob': '',
            'height': '',
            'weight': '',
            'hair': '',
            'eyes': '',
            'case_numbers': []
        }
        
        # Get page content
        page_content = page.content()
        
        # Extract Total Bond
        total_bond_match = re.search(r'Total Bond:\s*\$?([\d,]+(?:\.\d{2})?)', page_content)
        if total_bond_match:
            result['total_bond'] = total_bond_match.group(1).replace(',', '')
            result['bond_amount'] = result['total_bond']
        
        # Try to find mugshot image
        try:
            img_elements = page.query_selector_all('img')
            for img in img_elements:
                src = img.get_attribute('src')
                if src and ('inmate' in src.lower() or 'photo' in src.lower() or 'image' in src.lower()):
                    if src.startswith('/'):
                        result['mugshot_url'] = f"https://apps.osceola.org{src}"
                    elif src.startswith('http'):
                        result['mugshot_url'] = src
                    break
        except:
            pass
        
        # Extract demographic info from table
        try:
            # Race
            race_match = re.search(r'Race:\s*</td>\s*<td[^>]*>\s*(\w+)', page_content)
            if race_match:
                result['race'] = race_match.group(1)
            
            # Sex
            sex_match = re.search(r'Sex:\s*</td>\s*<td[^>]*>\s*(\w+)', page_content)
            if sex_match:
                result['sex'] = sex_match.group(1)
            
            # DOB
            dob_match = re.search(r'DOB:\s*</td>\s*<td[^>]*>\s*([\d/]+)', page_content)
            if dob_match:
                result['dob'] = parse_date(dob_match.group(1))
            
            # Height
            height_match = re.search(r'Height:\s*</td>\s*<td[^>]*>\s*([^<]+)', page_content)
            if height_match:
                result['height'] = clean_text(height_match.group(1))
            
            # Weight
            weight_match = re.search(r'Weight:\s*</td>\s*<td[^>]*>\s*(\d+)', page_content)
            if weight_match:
                result['weight'] = weight_match.group(1)
        except:
            pass
        
        # Extract case numbers (Reference column)
        case_matches = re.findall(r'(\d{4}\s*(?:CF|CT|MM|TR)\s*\d+)', page_content)
        result['case_numbers'] = list(set(case_matches))
        
        return result
        
    except Exception as e:
        sys.stderr.write(f"   Error scraping detail page for {inmate_id}: {e}\n")
        return None


def scrape_daily_report(page, target_date):
    """
    Scrape all inmates from a specific date's daily report.
    Returns list of record dictionaries.
    """
    records = []
    
    # Format date for URL/dropdown
    date_str = target_date.strftime('%m/%d/%Y')
    sys.stderr.write(f"📅 Scraping date: {date_str}\n")
    
    # Navigate to daily report
    base_url = "https://apps.osceola.org/Apps/CorrectionsReports/Report/Daily/"
    page.goto(base_url, wait_until='networkidle', timeout=30000)
    time.sleep(2)
    
    # Select the target date from dropdown
    try:
        date_select = page.query_selector('#date')
        if date_select:
            # Check if date is available in dropdown by checking option text
            options = page.query_selector_all('#date option')
            date_found = False
            for opt in options:
                opt_text = opt.inner_text().strip()
                if opt_text == date_str:
                    date_found = True
                    break
            
            if not date_found:
                sys.stderr.write(f"   ⚠️ Date {date_str} not available in dropdown\n")
                return records
            
            # Select by label (text) since value attribute is None
            date_select.select_option(label=date_str)
            time.sleep(2)
            page.wait_for_load_state('networkidle')
    except Exception as e:
        sys.stderr.write(f"   Error selecting date: {e}\n")
        return records
    
    # Get all inmate links from the table
    try:
        # Find all name links (they link to detail pages)
        inmate_links = page.query_selector_all('table a[href*="Details"]')
        
        sys.stderr.write(f"   Found {len(inmate_links)} inmates\n")
        
        # Extract basic info from listing page first
        inmates_basic = []
        
        for link in inmate_links:
            try:
                href = link.get_attribute('href')
                inmate_id_match = re.search(r'/Details/(\d+)', href)
                if not inmate_id_match:
                    continue
                
                inmate_id = inmate_id_match.group(1)
                name_text = clean_text(link.inner_text())
                
                # Get the parent row to extract other info
                row = link.evaluate('el => el.closest("tr")')
                if row:
                    row_element = page.query_selector(f'tr:has(a[href*="{inmate_id}"])')
                    if row_element:
                        row_text = row_element.inner_text()
                        
                        # Extract booking number
                        booking_match = re.search(r'Booking #:\s*(\d+)', row_text)
                        booking_num = booking_match.group(1) if booking_match else ""
                        
                        # Extract birthdate
                        dob_match = re.search(r'Birthdate:\s*([A-Za-z]+ \d+, \d{4})', row_text)
                        dob = parse_date(dob_match.group(1)) if dob_match else ""
                        
                        # Extract agency
                        agency_match = re.search(r'By Agency:\s*(\w+)', row_text)
                        agency = agency_match.group(1) if agency_match else "OCSO"
                        
                        # Extract charges (last column typically)
                        cells = row_element.query_selector_all('td')
                        charges_text = ""
                        if len(cells) >= 3:
                            charges_text = clean_text(cells[-1].inner_text())
                        
                        inmates_basic.append({
                            'inmate_id': inmate_id,
                            'name': name_text,
                            'booking_number': booking_num,
                            'dob': dob,
                            'agency': agency,
                            'charges_summary': charges_text,
                            'arrest_date': date_str
                        })
                    
            except Exception as e:
                sys.stderr.write(f"   Error parsing inmate link: {e}\n")
                continue
        
        # Now visit each detail page to get bond amounts
        for i, basic in enumerate(inmates_basic):
            sys.stderr.write(f"   [{i+1}/{len(inmates_basic)}] Getting details for {basic['name']}...\n")
            
            detail = scrape_detail_page(page, basic['inmate_id'])
            
            if detail:
                full_name, first_name, last_name = parse_name(basic['name'])
                
                record = {
                    'Booking_Number': basic['booking_number'],
                    'Full_Name': full_name,
                    'First_Name': first_name,
                    'Last_Name': last_name,
                    'DOB': detail.get('dob') or basic['dob'],
                    'Sex': detail.get('sex', ''),
                    'Race': detail.get('race', ''),
                    'Arrest_Date': basic['arrest_date'],
                    'Arrest_Time': '',
                    'Booking_Date': basic['arrest_date'],
                    'Booking_Time': '',
                    'Agency': basic['agency'],
                    'Address': '',
                    'City': '',
                    'State': 'FL',
                    'Zipcode': '',
                    'Charges': basic['charges_summary'],
                    'Bond_Amount': detail.get('bond_amount', ''),
                    'Bond_Type': '',
                    'Status': 'In Custody',
                    'Court_Date': '',
                    'Case_Number': ', '.join(detail.get('case_numbers', [])),
                    'Mugshot_URL': detail.get('mugshot_url', ''),
                    'County': 'Osceola',
                    'Court_Location': '',
                    'Detail_URL': f"https://apps.osceola.org/Apps/CorrectionsReports/Report/Details/{basic['inmate_id']}"
                }
                
                records.append(record)
            
            # Small delay between detail page requests
            time.sleep(0.5)
        
    except Exception as e:
        sys.stderr.write(f"   Error scraping daily report: {e}\n")
    
    return records


def scrape_osceola(start_date_str="12/10/2025", end_date_str=None):
    """
    Main scraper function for Osceola County.
    Scrapes from start_date to end_date (or today if not specified).
    """
    sys.stderr.write("🏛️ Starting Osceola County Scraper\n")
    sys.stderr.write(f"   Source: https://apps.osceola.org/Apps/CorrectionsReports/Report/Daily/\n")
    
    # Parse dates
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%m/%d/%Y')
    else:
        end_date = datetime.now()
    
    sys.stderr.write(f"   Date range: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}\n")
    
    all_records = []
    
    # Initialize browser with Playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            
            # Iterate through each date
            current_date = start_date
            while current_date <= end_date:
                try:
                    daily_records = scrape_daily_report(page, current_date)
                    all_records.extend(daily_records)
                    sys.stderr.write(f"   ✅ Got {len(daily_records)} records for {current_date.strftime('%m/%d/%Y')}\n")
                except Exception as e:
                    sys.stderr.write(f"   ❌ Error on {current_date.strftime('%m/%d/%Y')}: {e}\n")
                
                current_date += timedelta(days=1)
                time.sleep(1)  # Delay between dates
            
            browser.close()
            
        except Exception as e:
            sys.stderr.write(f"❌ Browser Error: {e}\n")
    
    sys.stderr.write(f"\n📊 Total records scraped: {len(all_records)}\n")
    
    # Output JSON to stdout
    print(json.dumps(all_records))
    
    return all_records


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Osceola County Arrest Scraper')
    parser.add_argument('--start', default='12/10/2025', help='Start date (MM/DD/YYYY)')
    parser.add_argument('--end', default=None, help='End date (MM/DD/YYYY), defaults to today')
    
    args = parser.parse_args()
    
    scrape_osceola(args.start, args.end)
