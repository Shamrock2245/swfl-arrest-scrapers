#!/usr/bin/env python3
"""
Polk County Jail Inquiry Scraper
https://polksheriff.org/detention/jail-inquiry

Uses Selenium to:
1. Navigate to the Polk County jail inquiry page
2. Search with yesterday's date (website has no entries for today)
3. Click each booking number to get detail page data (charges, bond)
4. Output JSON to stdout
"""

import sys
import json
import time
import re
import os
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

BASE_URL = "https://polksheriff.org"
SEARCH_URL = f"{BASE_URL}/detention/jail-inquiry"


def parse_name(full_name: str) -> dict:
    """Parse full name into first, middle, last components."""
    result = {'Full_Name': full_name, 'First_Name': '', 'Middle_Name': '', 'Last_Name': ''}
    if not full_name:
        return result
    
    # Format: "LAST, FIRST MIDDLE" or "LAST, FIRST"
    if ',' in full_name:
        parts = full_name.split(',', 1)
        result['Last_Name'] = parts[0].strip()
        if len(parts) > 1:
            first_parts = parts[1].strip().split()
            if first_parts:
                result['First_Name'] = first_parts[0]
                if len(first_parts) > 1:
                    result['Middle_Name'] = ' '.join(first_parts[1:])
    return result


def parse_detail_page(driver, booking_number: str) -> dict:
    """Extract all data from an inmate detail page."""
    record = {
        'County': 'Polk',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Booking_Number': booking_number,
        'State': 'FL',
    }
    
    try:
        # Wait for page to load
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Get full page text for pattern matching
        text_content = soup.get_text(' ', strip=True)
        
        # === Extract name ===
        # Look for name pattern in the profile area
        name_match = re.search(r'([A-Z]+,\s*[A-Z]+(?:\s+[A-Z]+)?)\s*Booking\s*Number:', text_content, re.I)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = parse_name(full_name)
            record.update(name_parts)
        else:
            # Try alternate pattern - look for name after INMATE PROFILE
            name_match2 = re.search(r'INMATE\s*PROFILE\s+([A-Z]+,\s*[A-Z]+(?:\s+[A-Z]+)?)', text_content, re.I)
            if name_match2:
                full_name = name_match2.group(1).strip()
                name_parts = parse_name(full_name)
                record.update(name_parts)
        
        # Race/Sex
        race_sex_match = re.search(r'Race/Sex:\s*([A-Z]+/[A-Z])', text_content, re.I)
        if race_sex_match:
            rs = race_sex_match.group(1).split('/')
            record['Race'] = rs[0] if len(rs) > 0 else ''
            record['Sex'] = rs[1] if len(rs) > 1 else ''
        
        # DOB
        dob_match = re.search(r'DOB:\s*(\d{1,2}/\d{1,2}/\d{4})', text_content, re.I)
        if dob_match:
            record['DOB'] = dob_match.group(1)
        
        # Height
        height_match = re.search(r'Height:\s*(\d+)', text_content, re.I)
        if height_match:
            record['Height'] = height_match.group(1)
        
        # Weight
        weight_match = re.search(r'Weight:\s*(\d+)', text_content, re.I)
        if weight_match:
            record['Weight'] = weight_match.group(1)
        
        # Booking Date
        booking_date_match = re.search(r'Booking\s*Date:\s*(\d{1,2}/\d{1,2}/\d{4})', text_content, re.I)
        if booking_date_match:
            record['Booking_Date'] = booking_date_match.group(1)
        
        # Location / Facility
        location_match = re.search(r'Location:\s*([A-Z]+)', text_content, re.I)
        if location_match:
            record['Facility'] = location_match.group(1)
        
        # Inmate Status
        status_match = re.search(r'Inmate\s*Status:\s*([A-Za-z\s-]+?)(?=Bond|Ready|Height|Weight|$)', text_content, re.I)
        if status_match:
            status_val = status_match.group(1).strip()
            if len(status_val) > 0 and len(status_val) < 30:
                record['Status'] = status_val
        
        # Mugshot URL
        img_tags = soup.find_all('img')
        for img in img_tags:
            src = img.get('src', '')
            alt = img.get('alt', '').lower()
            # Look for mugshot image
            if 'inmate' in src.lower() or 'photo' in src.lower() or 'mugshot' in alt:
                if not src.startswith('http'):
                    src = BASE_URL + src
                record['Mugshot_URL'] = src
                break
        
        # === CHARGES SECTION ===
        charges = []
        bond_amounts = []
        
        # Look for CHARGES header and table
        charges_header = soup.find(string=re.compile(r'^CHARGES$|^Charges$', re.I))
        if charges_header:
            # Find the table after the charges header
            parent = charges_header.find_parent()
            if parent:
                table = parent.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header row
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            # Usually: Charge Description, Bond Amount, etc.
                            charge_text = cells[0].get_text(strip=True) if cells else ''
                            if charge_text and not charge_text.lower().startswith('charge'):
                                charges.append(charge_text)
                            # Look for bond amount in this row
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                bond_match = re.search(r'\$\s*([\d,]+(?:\.\d{2})?)', cell_text)
                                if bond_match:
                                    try:
                                        amt = float(bond_match.group(1).replace(',', ''))
                                        bond_amounts.append(amt)
                                    except ValueError:
                                        pass
        
        # Fallback: look for charge patterns in full text
        if not charges:
            charge_patterns = re.findall(
                r'(\d{3}\.\d+[^|$]*)',  # Florida statute numbers
                text_content
            )
            for cp in charge_patterns[:10]:
                clean = cp.strip()
                if len(clean) > 5 and len(clean) < 200:
                    charges.append(clean)
        
        record['Charges'] = ' | '.join(charges[:10]) if charges else ''
        
        # === BOND SECTION ===
        # Look for total bond
        total_bond_match = re.search(r'(?:Total\s*)?Bond(?:\s*Amount)?:\s*\$?\s*([\d,]+(?:\.\d{2})?)', text_content, re.I)
        if total_bond_match:
            try:
                record['Bond_Amount'] = str(int(float(total_bond_match.group(1).replace(',', ''))))
            except ValueError:
                record['Bond_Amount'] = '0'
        elif bond_amounts:
            record['Bond_Amount'] = str(int(sum(bond_amounts)))
        else:
            record['Bond_Amount'] = '0'
        
        # Detail URL
        record['Detail_URL'] = driver.current_url
        
    except Exception as e:
        sys.stderr.write(f"⚠️ Error parsing detail page for {booking_number}: {e}\n")
    
    return record


def scrape_polk(days_back: int = 1):
    """
    Scrape Polk County jail inquiry.
    
    Args:
        days_back: Number of days to go back from today (default 1 = yesterday)
    """
    records = []
    
    # Calculate search date (yesterday by default)
    search_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    search_date_str = search_date.strftime("%m/%d/%Y")
    
    sys.stderr.write(f"ℹ️  Scraping Polk County for date: {search_date_str}\n")
    
    driver = None
    try:
        # Setup Selenium Chrome driver
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # Navigate to search page
        sys.stderr.write(f"📍 Navigating to {SEARCH_URL}\n")
        driver.get(SEARCH_URL)
        time.sleep(3)
        
        # Wait for page to load and look for Booking Date tab
        try:
            booking_date_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Booking Date')]"))
            )
            booking_date_tab.click()
            time.sleep(1)
            sys.stderr.write("📅 Clicked 'Booking Date' tab\n")
        except TimeoutException:
            sys.stderr.write("⚠️ Could not find 'Booking Date' tab\n")
        
        # Find date input and set value
        try:
            # Look for the date input field
            date_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input.k-input"))
            )
            # Set date via JavaScript to avoid interaction issues
            driver.execute_script("arguments[0].value = arguments[1]; arguments[0].dispatchEvent(new Event('change'));", date_input, search_date_str)
            sys.stderr.write(f"📅 Set date via JS: {search_date_str}\n")
        except TimeoutException:
            sys.stderr.write("⚠️ Could not find date input\n")
        
        time.sleep(1)
        
        # Click SEARCH button using specific ID to trigger the Kendo search
        try:
            # Attempt to click the button with id 'btnSearchDate'
            search_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "btnSearchDate"))
            )
            search_btn.click()
            sys.stderr.write("🔍 Clicked SEARCH button (by ID)\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ Click by ID failed: {e}. Trying generic JS click.\n")
            # Fallback: use JavaScript to click any submit/button element
            try:
                driver.execute_script("document.querySelector('button, input[type=submit]').click();")
                sys.stderr.write("🔍 Clicked SEARCH button via JS fallback\n")
            except Exception as js_e:
                sys.stderr.write(f"❌ JS click also failed: {js_e}\n")
                return []

        # Wait for results: either a table with rows or a 'no records' message
        try:
            WebDriverWait(driver, 15).until(
                EC.any_of(
                    EC.presence_of_element_located((By.TAG_NAME, "table")),
                    EC.presence_of_element_located((By.CLASS_NAME, "k-grid-norecords"))
                )
            )
            sys.stderr.write("📊 Results container loaded\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ Results not loaded: {e}\n")
            return []

        time.sleep(5)  # Wait for any additional loading

        # Parse results table
        sys.stderr.write("\n📄 Processing results...\n")
        
        html = driver.page_source
        # Save debug HTML to see what's being parsed
        try:
            with open('/tmp/polk_results_debug.html', 'w', encoding='utf-8') as f:
                f.write(html)
            sys.stderr.write("💾 Saved debug HTML to /tmp/polk_results_debug.html\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ Could not save debug HTML: {e}\n")


        # Parse results table
        sys.stderr.write("\n📄 Processing results...\n")
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all booking number links
        booking_links = []
        
        # Check for 'no records' first
        if soup.find(class_="k-grid-norecords"):
            sys.stderr.write("ℹ️  No records found for this date.\n")
            return []

        # Look for table with booking info
        # The data is usually in a div with id="jail-grid" containing a table
        jail_grid = soup.find(id="jail-grid")
        if jail_grid:
            table = jail_grid.find('table')
            if table:
                rows = table.find_all('tr')
                sys.stderr.write(f"📊 Found grid table with {len(rows)} rows\n")
                for row in rows:
                    cells = row.find_all('td')
                    if cells:
                        link = cells[0].find('a')
                        if link:
                            href = link.get('href', '')
                            booking_num = link.get_text(strip=True)
                            if href and booking_num.isdigit():
                                if not href.startswith('http'):
                                    href = BASE_URL + href
                                booking_links.append((booking_num, href))

        # Fallback: look for any links with booking number pattern if grid parsing failed
        if not booking_links:
            sys.stderr.write("⚠️ Grid parsing returned no links, attempting fallback...\n")
            for link in soup.find_all('a', href=re.compile(r'inmate|profile', re.I)):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if re.match(r'^\d+$', text):
                    if not href.startswith('http'):
                        href = BASE_URL + href
                    booking_links.append((text, href))
        
        sys.stderr.write(f"   Found {len(booking_links)} booking links\n")
        
        # Visit each detail page
        for idx, (booking_num, detail_url) in enumerate(booking_links):
            try:
                sys.stderr.write(f"   [{idx+1}/{len(booking_links)}] Scraping {booking_num}...")
                
                driver.get(detail_url)
                # Wait for detail profile to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Booking Number:')]"))
                )
                
                record = parse_detail_page(driver, booking_num)
                
                if record.get('Full_Name') or record.get('Charges'):
                    records.append(record)
                    sys.stderr.write(f" ✅\n")
                else:
                    # Still add the record with basic info
                    records.append(record)
                    sys.stderr.write(f" ⚠️ (partial data)\n")
                
            except Exception as e:
                sys.stderr.write(f" ❌ Error: {e}\n")
        
        sys.stderr.write(f"\n✅ Total records extracted: {len(records)}\n")
        
        # Output JSON to stdout
        if records:
            print(json.dumps(records, indent=2))
        
    except Exception as e:
        sys.stderr.write(f"❌ Critical error: {e}\n")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return records


if __name__ == "__main__":
    # Use 2 days back as a safer historical date for testing
    days_back = 2
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except ValueError:
            pass
    
    scrape_polk(days_back=days_back)

