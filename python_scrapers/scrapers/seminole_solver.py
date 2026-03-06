#!/usr/bin/env python3
"""
Seminole County Arrest Scraper
Source: https://seminole.northpointesuite.com/custodyportal
System: NorthPointe Suite Custody Portal (JavaScript-rendered)

This scraper uses Selenium to handle the JavaScript-rendered inmate portal.
It extracts inmate data from the search results page and optionally fetches
detailed booking/charge information from individual detail pages.

Known Limitations:
- Results limited to 500 inmates per search
- Requires JavaScript rendering (Selenium/Chromium)
- Detail page fetching is slow (1-2 seconds per inmate)
"""

import sys
import json
import re
import time
import html
from datetime import datetime
from bs4 import BeautifulSoup

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import StaleElementReferenceException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
except ImportError:
    sys.stderr.write("❌ Selenium not installed. Run: pip install selenium webdriver-manager\n")
    print("[]")
    sys.exit(1)


def setup_browser():
    """Configure and return a headless Chrome browser instance"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Use system chromium
    options.binary_location = '/usr/bin/chromium-browser'
    
    # Use webdriver-manager to get chromedriver
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(60)
    return driver


def extract_records_from_page_source(page_source):
    """
    Extract inmate records directly from page source HTML.
    The data is embedded in JavaScript goToDetails calls.
    """
    records = []
    
    # Find all goToDetails JSON objects in the page source
    # They appear as: javascript:goToDetails({...})
    # But HTML entities are encoded, so we need to handle &quot; etc.
    
    # First, decode HTML entities
    decoded_source = html.unescape(page_source)
    
    # Find all goToDetails calls
    pattern = r'javascript:goToDetails\((\{[^}]+\})\)'
    matches = re.findall(pattern, decoded_source)
    
    for match in matches:
        try:
            data = json.loads(match)
            
            # Build full name
            first = data.get('firstName', '') or ''
            last = data.get('lastName', '') or ''
            middle = data.get('middleName', '') or ''
            
            if middle:
                full_name = f"{last}, {first}, {middle}"
            else:
                full_name = f"{last}, {first}"
            
            record = {
                'County': 'Seminole',
                'State': 'FL',
                'Status': 'In Custody',
                'Full_Name': full_name.upper(),
                'Last_Name': last.upper(),
                'First_Name': first.upper(),
                'Middle_Name': middle.upper() if middle else '',
                'Age': str(data.get('age', '')),
                'Sex': data.get('gender', ''),
                'Race': data.get('race', ''),
                'Height': data.get('height', ''),
                'Weight': data.get('weight', ''),
                'Hair_Color': data.get('hairColor', ''),
                'Eye_Color': data.get('eyeColor', ''),
                'Inmate_Number': str(data.get('personId', '')),
                'Booking_Number': str(data.get('personId', '')),  # Use personId as booking number
                'Booking_Date': '',
                'Arrest_Agency': '',
                'Bond_Amount': '',
                'Charges': '',
                'Facility': 'John E Polk Correctional Facility',
                'Detail_URL': '',
                'Mugshot_URL': '',
                'DOB': ''
            }
            
            # Parse DOB
            dob = data.get('dateOfBirth', '')
            if dob:
                try:
                    dob_date = datetime.fromisoformat(dob.replace('Z', '+00:00'))
                    record['DOB'] = dob_date.strftime('%m/%d/%Y')
                except Exception:
                    pass
            
            records.append(record)
            
        except json.JSONDecodeError:
            continue
        except Exception:
            continue
    
    return records


def fetch_detail_page(driver, person_id):
    """
    Navigate to detail page and extract booking/charge information.
    Returns dict with additional fields.
    """
    details = {}
    
    try:
        # Navigate directly to detail page URL
        detail_url = f"https://seminole.northpointesuite.com/custodyportal/details/{person_id}"
        driver.get(detail_url)
        time.sleep(2)
        
        details['Detail_URL'] = detail_url
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Helper to find value by label
        def get_val(label_text):
            # Look for <td>Label</td> <td>Value</td>
            label = soup.find('td', string=re.compile(label_text, re.I))
            if label:
                val = label.find_next_sibling('td')
                if val: return val.get_text(strip=True)
            return None

        # Booking Number
        bn = get_val('Booking Number') or get_val('Booking #')
        if bn: details['Booking_Number'] = bn
        
        # Booking Date
        bd = get_val('Booking Date')
        if bd: details['Booking_Date'] = bd
        
        # Arrest Date (often same as booking, but check specific label)
        ad = get_val('Arrest Date')
        if ad: details['Arrest_Date'] = ad

        # Arresting Agency
        aa = get_val('Arresting Agency')
        if aa: details['Arrest_Agency'] = aa
        
        # Total Bond
        tb = get_val('Total Bond')
        if tb: 
            details['Bond_Amount'] = tb.replace('$', '').replace(',', '')
        
        # Status
        st = get_val('Status')
        if st: details['Status'] = st
        
        # Charges - Look for the Charges table
        # Attempt to find table with header "Offense" or "Statute"
        charges = []
        tables = soup.find_all('table')
        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all('th')]
            if any(x in headers for x in ['offense', 'statute', 'charge']):
                # This is likely the charges table
                rows = table.find_all('tr')[1:] # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # Extract text from all cells to form charge string
                        # Usually: counts, statute, description, degree, etc.
                        charge_parts = [c.get_text(strip=True) for c in cells if c.get_text(strip=True)]
                        if charge_parts:
                            charges.append(" ".join(charge_parts))
        
        if charges:
            details['Charges'] = ' | '.join(charges)
        
    except Exception as e:
        sys.stderr.write(f"      ⚠️ Detail fetch error: {e}\n")
    
    return details


def scrape_seminole(fetch_details=True, max_detail_records=100):
    """
    Main scraper function for Seminole County.
    
    Args:
        fetch_details: If True, fetch detailed booking/charge info (slower)
        max_detail_records: Maximum number of records to fetch details for
    """
    sys.stderr.write("🔵 Starting Seminole County Scraper (Selenium)\n")
    
    url = "https://seminole.northpointesuite.com/custodyportal"
    records = []
    driver = None
    
    try:
        sys.stderr.write(f"📡 Launching browser and navigating to {url}...\n")
        driver = setup_browser()
        driver.get(url)
        time.sleep(5)
        
        # Click Search button
        sys.stderr.write("🔍 Searching for current inmates...\n")
        
        search_btn = driver.find_element(By.ID, "searchBtn")
        driver.execute_script("arguments[0].click();", search_btn)
        
        # Wait for results to load
        for i in range(15):
            time.sleep(2)
            try:
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if 'Searching...' not in body_text:
                    results_match = re.search(r'Search Results \((\d+)\)', body_text)
                    if results_match and int(results_match.group(1)) > 0:
                        sys.stderr.write(f"   Results loaded: {results_match.group(1)} inmates\n")
                        break
            except WebDriverException:
                sys.stderr.write(f"   Waiting for page... ({i*2}s)\n")
                continue
        
        time.sleep(3)
        
        # Extract records from page source
        sys.stderr.write("📋 Extracting inmate data from page source...\n")
        page_source = driver.page_source
        records = extract_records_from_page_source(page_source)
        sys.stderr.write(f"   Found {len(records)} inmates\n")
        
        # Optionally fetch detail pages for booking/charge info
        if fetch_details and records:
            sys.stderr.write(f"📄 Fetching detail pages (up to {max_detail_records} records)...\n")
            
            for i, record in enumerate(records[:max_detail_records]):
                try:
                    name = record['Full_Name']
                    person_id = record.get('Inmate_Number', '')
                    
                    if not person_id:
                        continue
                    
                    sys.stderr.write(f"   [{i+1}/{min(len(records), max_detail_records)}] {name}\n")
                    
                    details = fetch_detail_page(driver, person_id)
                    record.update(details)
                    
                except Exception as e:
                    sys.stderr.write(f"      ⚠️ Error: {e}\n")
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
    
    sys.stderr.write(f"📊 Extracted {len(records)} records\n")
    print(json.dumps(records))


if __name__ == "__main__":
    # Run with detail fetching for first 100 records
    # Set fetch_details=False for faster extraction without charges/bond
    scrape_seminole(fetch_details=True, max_detail_records=100)
