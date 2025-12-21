import sys
import json
import time
import re
import os
import datetime
from DrissionPage import ChromiumPage, ChromiumOptions
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

def clean_charge_text(raw_charge):
    if not raw_charge:
        return ''
    return raw_charge.strip()

def parse_results_table(soup):
    """Parse arrest records from the BeautifulSoup object of a results page."""
    records = []
    
    # Find the main results table
    results_table = soup.find('table', class_='table-striped')
    if not results_table:
        return records
    
    # Find header row to skip it
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
                    
                    # Next rows have address, release info, and charges
                    # Look for ADDRESS row
                    if i + 1 < len(all_rows):
                        addr_row = all_rows[i + 1]
                        addr_cells = addr_row.find_all('td')
                        for cell in addr_cells:
                            text = cell.get_text(strip=True)
                            if text.startswith('ADDRESS:'):
                                record['Address'] = text.replace('ADDRESS:', '').strip()
                            elif text.startswith('CITY:'):
                                record['City'] = text.replace('CITY:', '').strip()
                    
                    # Look for RELEASE DATE row
                    if i + 2 < len(all_rows):
                        rel_row = all_rows[i + 2]
                        rel_cells = rel_row.find_all('td')
                        for cell in rel_cells:
                            text = cell.get_text(strip=True)
                            if text.startswith('RELEASE DATE:'):
                                record['Booking_Date'] = text.replace('RELEASE DATE:', '').strip()
                            elif text.startswith('RELEASE CODE:'):
                                code = text.replace('RELEASE CODE:', '').strip()
                                record['Bond_Type'] = code
                                if 'BOND' in code.upper():
                                    record['Status'] = 'RELEASED'
                    
                    # Look for charges in nested table
                    charges = []
                    case_numbers = []
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
                                    if len(charge_cells) >= 4:
                                        case_num = charge_cells[3].get_text(strip=True)
                                        if case_num and '-' in case_num and case_num not in case_numbers:
                                            case_numbers.append(case_num)
                    
                    record['Charges'] = ' | '.join(charges) if charges else ''
                    if case_numbers:
                        record['Case_Number'] = case_numbers[0]
                    
                    record['State'] = 'FL'
                    records.append(record)
                    
                    # Skip the related rows (4 rows per inmate)
                    i += 4
                    continue
            
            i += 1
            
        except Exception as e:
            i += 1
    
    return records

def scrape_hillsborough(days_back=3):
    """
    Scrape Hillsborough County (HCSO) with DrissionPage & Authorized Member Login
    """
    records = []
    
    # Get credentials from environment
    hcso_email = os.getenv('HCSO_EMAIL')
    hcso_password = os.getenv('HCSO_PASSWORD')
    
    if not hcso_email or not hcso_password:
        sys.stderr.write("❌ HCSO_EMAIL and HCSO_PASSWORD must be set in .env\n")
        return []
    
    end_date = time.strftime("%m/%d/%Y")
    # For now, let's just do a small range or what the user asked
    # Calculate start date
    import datetime
    start_dt = datetime.datetime.now() - datetime.timedelta(days=days_back)
    start_date = start_dt.strftime("%m/%d/%Y")

    sys.stderr.write(f"ℹ️  Scraping HCSO from {start_date} to {end_date}\n")
    
    # Persistent browser profile path for storing login session
    profile_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'hcso_profile')
    os.makedirs(profile_path, exist_ok=True)
    
    try:
        # Try to connect to existing Chrome (where user is already logged in)
        # First, check if Chrome is running with debug port
        import socket
        debug_port = 9222
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', debug_port))
        sock.close()
        
        co = ChromiumOptions()
        
        if result == 0:
            # Chrome is running with debug port - connect to it
            sys.stderr.write("🔗 Connecting to existing Chrome session...\n")
            co.set_local_port(debug_port)
        else:
            # No existing Chrome with debug port - need to start fresh
            sys.stderr.write("⚠️  No existing Chrome debug session found.\n")
            sys.stderr.write("   Please close all Chrome windows and run this command first:\n")
            sys.stderr.write('   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 &\n')
            sys.stderr.write("   Then log into HCSO in that Chrome window, and run this scraper again.\n")
            return []
        
        page = ChromiumPage(co)
        
        # Show current URL for debug
        current_url = page.url
        sys.stderr.write(f"📍 Current page: {current_url}\n")
        
        # Get the page HTML to check what's there
        page_html = page.html
        
        # Check for existing search results (look for the results table or header)
        # The results are in the page HTML, just need to scroll or look for the right element
        has_results = 'Search Results' in page_html or 'Booking Name' in page_html
        is_logged_in = 'Log out' in page_html or 'Welcome' in page_html
        
        if has_results:
            sys.stderr.write("✅ Found search results in page - scraping...\n")
        elif is_logged_in:
            sys.stderr.write("⚠️  Logged in but no search results visible. Please:\n")
            sys.stderr.write("   1. Perform a search in the Chrome window\n")
            sys.stderr.write("   2. Run this scraper again when results are showing\n")
            return []
        else:
            sys.stderr.write("❌ Not logged in. Please:\n")
            sys.stderr.write("   1. Log into HCSO in the Chrome window\n")
            sys.stderr.write("   2. Perform a search manually\n")
            sys.stderr.write("   3. Run this scraper again when results are showing\n")
            return []
        
        # DEBUG: Snapshot
        page.get_screenshot(path='hcso_results_debug.png', full_page=True)
        with open('hcso_results_debug.html', 'w') as f:
            f.write(page_html)
        sys.stderr.write("📸 Saved debug screenshot and HTML\n")

        # Parse results with pagination support
        from bs4 import BeautifulSoup
        all_records = []
        current_page = 1
        max_pages = 20  # Safety limit
        
        while current_page <= max_pages:
            sys.stderr.write(f"📄 Scraping page {current_page}...\n")
            
            # Get fresh page HTML
            page_html = page.html
            soup = BeautifulSoup(page_html, 'html.parser')
            
            # Check pagination info to get total pages
            pagination_info = soup.find('span', class_='paginationLeft')
            if pagination_info:
                info_text = pagination_info.get_text(strip=True)
                sys.stderr.write(f"   {info_text}\n")
            
            # Find the main results table
            results_table = soup.find('table', class_='table-striped')
            if not results_table:
                sys.stderr.write("⚠️ Could not find results table\n")
                break
            
            # Parse records from this page
            page_records = parse_results_table(soup)
            if not page_records:
                sys.stderr.write("   No records found on this page\n")
                break
                
            all_records.extend(page_records)
            sys.stderr.write(f"   ✅ Parsed {len(page_records)} records (total: {len(all_records)})\n")
            
            # Check for Next button
            next_btn = page.ele('text:Next >', timeout=2)
            if next_btn:
                # Check if it's disabled
                btn_class = next_btn.attr('class') or ''
                if 'disabled' in btn_class:
                    sys.stderr.write("   📄 Reached last page\n")
                    break
                
                # Click next
                next_btn.click()
                time.sleep(3)  # Wait for page to load
                current_page += 1
            else:
                sys.stderr.write("   📄 No more pages\n")
                break
        
        records = all_records
        sys.stderr.write(f"✅ Total extracted: {len(records)} records\n")
        
        if records:
            print(json.dumps(records, indent=2))
        else:
            sys.stderr.write("⚠️  No records extracted.\n")

    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    scrape_hillsborough()
