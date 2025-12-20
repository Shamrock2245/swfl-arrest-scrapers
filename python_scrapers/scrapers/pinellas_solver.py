"""
Pinellas County Sheriff - Who's in Jail Scraper
Source: https://www.pinellassheriff.gov/InmateBooking
County: Pinellas
Limitations: Requires Selenium for JavaScript rendering, searches by booking date
"""

import json
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def create_driver():
    """Create a headless Chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = '/usr/bin/chromium-browser'
    
    service = Service('/usr/local/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def parse_name(name_str: str) -> Dict[str, str]:
    """Parse 'LAST, FIRST MIDDLE' into components."""
    result = {'full_name': name_str, 'first_name': '', 'last_name': '', 'middle_name': ''}
    
    if ',' in name_str:
        parts = name_str.split(',', 1)
        result['last_name'] = parts[0].strip()
        if len(parts) > 1:
            first_parts = parts[1].strip().split()
            if first_parts:
                result['first_name'] = first_parts[0]
                if len(first_parts) > 1:
                    result['middle_name'] = ' '.join(first_parts[1:])
    
    return result


def parse_race_sex(race: str, sex: str) -> Dict[str, str]:
    """Parse race and sex codes."""
    race_map = {'B': 'Black', 'W': 'White', 'H': 'Hispanic', 'A': 'Asian', 'O': 'Other'}
    sex_map = {'M': 'Male', 'F': 'Female'}
    
    return {
        'race': race_map.get(race, race),
        'sex': sex_map.get(sex, sex)
    }


def scrape_pinellas(days_back: int = 7, fetch_details: bool = True) -> List[Dict[str, Any]]:
    """
    Scrape Pinellas County jail bookings by date.
    
    Args:
        days_back: Number of days to go back from today
        fetch_details: Whether to fetch detail pages for bond/charge info
    
    Returns:
        List of inmate records
    """
    print(f"🔵 Pinellas County Scraper Starting")
    print(f"   Scraping {days_back} days of bookings")
    
    driver = create_driver()
    all_inmates = {}  # Use dict to dedupe by name+dob
    
    try:
        # Navigate directly to the iframe URL
        base_url = "https://www.pinellassheriff.gov/InmateBooking"
        
        # Iterate through each date
        for day_offset in range(days_back):
            target_date = datetime.now() - timedelta(days=day_offset)
            date_str = target_date.strftime("%m/%d/%Y")
            print(f"\n📅 Searching bookings for {date_str}...")
            
            # Navigate to the page
            driver.get(base_url)
            time.sleep(3)
            
            try:
                # Use JavaScript to set form values (more reliable)
                driver.execute_script(f"document.getElementById('txtBookingDate').value = '{date_str}';")
                driver.execute_script("document.getElementById('chkIncludeCharge').checked = true;")
                
                # Set page size to 100
                try:
                    driver.execute_script("document.getElementById('drpPageSize').value = '100';")
                except:
                    pass
                
                # Click Search button via JavaScript
                driver.execute_script("document.getElementById('btnSearch').click();")
                time.sleep(3)
                
                # Parse results
                page_num = 1
                while True:
                    print(f"   Processing page {page_num}...")
                    
                    # Find results table
                    try:
                        results_table = driver.find_element(By.ID, "dgResults")
                        rows = results_table.find_elements(By.TAG_NAME, "tr")
                    except:
                        print(f"   No results found for {date_str}")
                        break
                    
                    if len(rows) <= 1:  # Only header row
                        print(f"   No results found for {date_str}")
                        break
                    
                    row_count = 0
                    # Parse each row (skip header)
                    for row in rows[1:]:
                        try:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) < 5:
                                continue
                            
                            # Get the link element which contains name and charge
                            try:
                                link = cells[0].find_element(By.TAG_NAME, "a")
                                link_text = link.text.strip()
                                link_href = link.get_attribute("href")
                            except:
                                continue
                            
                            # Get other fields
                            race = cells[1].text.strip() if len(cells) > 1 else ''
                            sex = cells[2].text.strip() if len(cells) > 2 else ''
                            dob = cells[3].text.strip() if len(cells) > 3 else ''
                            booking_info = cells[4].text.strip() if len(cells) > 4 else ''
                            
                            # Parse booking date/time and location
                            booking_date = ''
                            booking_time = ''
                            status = ''
                            if booking_info:
                                lines = booking_info.split('\n')
                                if lines:
                                    datetime_str = lines[0].strip()
                                    try:
                                        dt = datetime.strptime(datetime_str, "%m/%d/%Y %I:%M:%S %p")
                                        booking_date = dt.strftime("%m/%d/%Y")
                                        booking_time = dt.strftime("%I:%M:%S %p")
                                    except:
                                        booking_date = datetime_str
                                if len(lines) > 1:
                                    status = lines[1].strip()
                            
                            # Parse name and charge from link text
                            # The link text contains both name and charge on separate lines
                            link_lines = link_text.split('\n')
                            name_part = link_lines[0].strip() if link_lines else link_text
                            charge_part = link_lines[1].strip() if len(link_lines) > 1 else ''
                            
                            # Parse the name
                            name_info = parse_name(name_part)
                            race_sex_info = parse_race_sex(race, sex)
                            
                            # Create unique key
                            unique_key = f"{name_info['full_name']}_{dob}"
                            
                            if unique_key not in all_inmates:
                                all_inmates[unique_key] = {
                                    'full_name': name_info['full_name'],
                                    'first_name': name_info['first_name'],
                                    'last_name': name_info['last_name'],
                                    'middle_name': name_info.get('middle_name', ''),
                                    'dob': dob,
                                    'race': race_sex_info['race'],
                                    'sex': race_sex_info['sex'],
                                    'booking_date': booking_date,
                                    'booking_time': booking_time,
                                    'status': status,
                                    'charges': [charge_part] if charge_part else [],
                                    'detail_url': link_href,
                                    'county': 'Pinellas'
                                }
                                row_count += 1
                            else:
                                # Add charge to existing record
                                if charge_part and charge_part not in all_inmates[unique_key]['charges']:
                                    all_inmates[unique_key]['charges'].append(charge_part)
                            
                        except Exception as e:
                            continue
                    
                    print(f"   Found {row_count} new inmates on page {page_num}")
                    
                    # Check for next page
                    try:
                        pager_links = driver.find_elements(By.CSS_SELECTOR, "tr.pager a")
                        next_page = None
                        for link in pager_links:
                            if link.text.strip() == str(page_num + 1):
                                next_page = link
                                break
                        
                        if next_page:
                            driver.execute_script("arguments[0].click();", next_page)
                            time.sleep(2)
                            page_num += 1
                        else:
                            break
                    except:
                        break
                
                print(f"   Total unique inmates so far: {len(all_inmates)}")
                
            except Exception as e:
                print(f"   Error searching date {date_str}: {e}")
                continue
        
        # Optionally fetch detail pages for more info
        if fetch_details and all_inmates:
            print(f"\n📡 Fetching detail pages for bond amounts...")
            
            detail_count = 0
            for key, inmate in all_inmates.items():
                if detail_count >= 50:  # Limit detail fetches
                    print(f"   Limiting to 50 detail fetches")
                    break
                
                if inmate.get('detail_url'):
                    try:
                        driver.get(inmate['detail_url'])
                        time.sleep(1)
                        
                        page_source = driver.page_source
                        
                        # Look for bond amount
                        bond_match = re.search(r'Bond[:\s]*\$?([\d,]+\.?\d*)', page_source, re.IGNORECASE)
                        if bond_match:
                            inmate['bond_amount'] = bond_match.group(1).replace(',', '')
                        
                        # Look for docket number
                        docket_match = re.search(r'Docket[:\s#]*(\d+)', page_source, re.IGNORECASE)
                        if docket_match:
                            inmate['booking_number'] = docket_match.group(1)
                        
                        detail_count += 1
                        if detail_count % 10 == 0:
                            print(f"   Processed {detail_count} detail pages")
                        
                    except Exception as e:
                        continue
        
        print(f"\n✅ Pinellas County scraping complete")
        print(f"   Total unique inmates: {len(all_inmates)}")
        
        return list(all_inmates.values())
        
    finally:
        driver.quit()


def main():
    """Main entry point."""
    inmates = scrape_pinellas(days_back=3, fetch_details=False)
    print(json.dumps(inmates[:5], indent=2))
    return inmates


if __name__ == "__main__":
    main()
