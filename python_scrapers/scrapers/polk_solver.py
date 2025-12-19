#!/usr/bin/env python3
"""
Polk County Arrest Scraper
Source: https://www.polksheriff.org/detention/jail-inquiry
System: Custom ASP.NET/Kendo UI jail inquiry system

This scraper uses Selenium to handle the JavaScript-rendered jail inquiry page.
It searches by common last names with "Current inmates only" checked to get all current inmates.

Known Limitations:
- No way to get all inmates at once - must search by name
- Results are paginated (20 per page)
- Requires JavaScript rendering (Selenium/Chromium)
"""

import sys
import json
import re
import time
from datetime import datetime

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
except ImportError:
    sys.stderr.write("❌ Selenium not installed. Run: pip install selenium webdriver-manager\n")
    print("[]")
    sys.exit(1)


# Common last names to search - covers a large portion of inmates
COMMON_LAST_NAMES = [
    'SMITH', 'JOHNSON', 'WILLIAMS', 'BROWN', 'JONES', 'GARCIA', 'MILLER', 'DAVIS',
    'RODRIGUEZ', 'MARTINEZ', 'HERNANDEZ', 'LOPEZ', 'GONZALEZ', 'WILSON', 'ANDERSON',
    'THOMAS', 'TAYLOR', 'MOORE', 'JACKSON', 'MARTIN', 'LEE', 'PEREZ', 'THOMPSON',
    'WHITE', 'HARRIS', 'SANCHEZ', 'CLARK', 'RAMIREZ', 'LEWIS', 'ROBINSON', 'WALKER',
    'YOUNG', 'ALLEN', 'KING', 'WRIGHT', 'SCOTT', 'TORRES', 'NGUYEN', 'HILL', 'FLORES',
    'GREEN', 'ADAMS', 'NELSON', 'BAKER', 'HALL', 'RIVERA', 'CAMPBELL', 'MITCHELL',
    'CARTER', 'ROBERTS'
]


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


def extract_table_records(driver):
    """
    Extract inmate records from the results table.
    
    Returns:
        List of inmate record dictionaries
    """
    records = []
    
    try:
        # Wait for table to be present
        time.sleep(2)
        
        # Check if there are results
        page_source = driver.page_source
        if 'No items to display' in page_source:
            return []
        
        # Find all table rows in the grid
        rows = driver.find_elements(By.CSS_SELECTOR, "table[role='treegrid'] tbody tr")
        
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 8:
                    # Note: First cell is empty (checkbox column), so indices are offset by 1
                    # Row format: ['', booking#, name, RS, DOB, entry_date, release_date, location]
                    booking_num = cells[1].text.strip()
                    name = cells[2].text.strip()
                    rs = cells[3].text.strip()  # Race/Sex
                    dob = cells[4].text.strip()
                    entry_date = cells[5].text.strip()
                    release_date = cells[6].text.strip()
                    location = cells[7].text.strip()
                    
                    # Skip header row or empty rows
                    if not booking_num or booking_num == 'Booking #':
                        continue
                    
                    # Parse race and sex
                    race = ''
                    sex = ''
                    if rs and len(rs) >= 2:
                        race = rs[0]  # First character is race (W, B, H, etc.)
                        sex = rs[1]   # Second character is sex (M, F)
                    
                    # Parse name (format: LAST, FIRST MIDDLE)
                    name_parts = name.split(',', 1)
                    last_name = name_parts[0].strip() if name_parts else ''
                    first_middle = name_parts[1].strip() if len(name_parts) > 1 else ''
                    
                    # Split first and middle name
                    first_parts = first_middle.split(' ', 1)
                    first_name = first_parts[0].strip() if first_parts else ''
                    middle_name = first_parts[1].strip() if len(first_parts) > 1 else ''
                    
                    # Determine status
                    status = 'Released' if release_date else 'In Custody'
                    
                    record = {
                        'County': 'Polk',
                        'State': 'FL',
                        'Booking_Number': booking_num,
                        'Full_Name': name,
                        'Last_Name': last_name,
                        'First_Name': first_name,
                        'Middle_Name': middle_name,
                        'DOB': dob,
                        'Race': race,
                        'Sex': sex,
                        'Booking_Date': entry_date,
                        'Status': status,
                        'Facility': location,
                        'Charges': '',
                        'Bond_Amount': '',
                        'Detail_URL': '',
                        'Mugshot_URL': ''
                    }
                    
                    records.append(record)
                    
            except Exception as e:
                continue
        
    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error extracting table: {e}\n")
    
    return records


def search_by_name(driver, last_name, current_only=True):
    """
    Search for inmates by last name.
    
    Args:
        driver: Selenium WebDriver instance
        last_name: Last name to search for
        current_only: If True, only search current inmates
    
    Returns:
        List of inmate records (all pages)
    """
    all_records = []
    
    try:
        # Enter last name
        last_name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "LastName"))
        )
        last_name_input.clear()
        last_name_input.send_keys(last_name)
        
        # Check "Current inmates only" checkbox if needed
        if current_only:
            try:
                # Find the checkbox by its label
                checkbox_label = driver.find_element(By.XPATH, "//label[contains(text(), 'Current inmates only')]")
                checkbox = checkbox_label.find_element(By.XPATH, "./preceding-sibling::input[@type='checkbox'] | ./input[@type='checkbox']")
                if not checkbox.is_selected():
                    checkbox_label.click()
                    time.sleep(0.5)
            except Exception:
                # Try clicking the label directly
                try:
                    label = driver.find_element(By.XPATH, "//label[contains(text(), 'Current inmates only')]")
                    label.click()
                    time.sleep(0.5)
                except Exception:
                    pass
        
        # Click search button
        search_btn = driver.find_element(By.ID, "btnSearchName")
        driver.execute_script("arguments[0].click();", search_btn)
        
        # Wait for results
        time.sleep(3)
        
        # Extract records from first page
        records = extract_table_records(driver)
        all_records.extend(records)
        
        # Check for pagination and get all pages
        while True:
            try:
                # Look for "next page" button
                next_btn = driver.find_element(By.CSS_SELECTOR, "a[title='Go to the next page'], a[aria-label='Go to the next page']")
                if 'k-state-disabled' in next_btn.get_attribute('class') or not next_btn.is_enabled():
                    break
                
                next_btn.click()
                time.sleep(2)
                
                # Extract records from this page
                records = extract_table_records(driver)
                if not records:
                    break
                    
                all_records.extend(records)
                
            except NoSuchElementException:
                break
            except Exception:
                break
        
    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error searching by name {last_name}: {e}\n")
    
    return all_records


def scrape_polk(max_names=50):
    """
    Main scraper function for Polk County.
    
    Args:
        max_names: Maximum number of common names to search
    """
    sys.stderr.write("🔵 Starting Polk County Scraper (Selenium)\n")
    
    url = "https://www.polksheriff.org/detention/jail-inquiry"
    all_records = []
    seen_bookings = set()
    driver = None
    
    try:
        sys.stderr.write(f"📡 Launching browser and navigating to {url}...\n")
        driver = setup_browser()
        driver.get(url)
        time.sleep(5)
        
        # Search by common last names
        names_to_search = COMMON_LAST_NAMES[:max_names]
        sys.stderr.write(f"🔍 Searching {len(names_to_search)} common last names for current inmates...\n")
        
        for i, name in enumerate(names_to_search):
            sys.stderr.write(f"   [{i+1}/{len(names_to_search)}] Searching '{name}'...\n")
            
            # Refresh page to reset state
            driver.get(url)
            time.sleep(3)
            
            records = search_by_name(driver, name, current_only=True)
            
            # Deduplicate by booking number
            new_count = 0
            for record in records:
                booking_num = record.get('Booking_Number', '')
                if booking_num and booking_num not in seen_bookings:
                    seen_bookings.add(booking_num)
                    all_records.append(record)
                    new_count += 1
            
            sys.stderr.write(f"      Found {len(records)} records ({new_count} new, {len(all_records)} total)\n")
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
    
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
    
    sys.stderr.write(f"📊 Extracted {len(all_records)} total unique records\n")
    print(json.dumps(all_records))


if __name__ == "__main__":
    # Search top 50 common names for current inmates
    scrape_polk(max_names=50)
