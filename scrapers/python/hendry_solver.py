import sys
import json
import time
import re
import os
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stderr.write("=== Hendry Solver Starting ===\n")
sys.stderr.flush()


def clean_charge_text(raw_charge):
    """Clean charge text to extract only the human-readable description."""
    if not raw_charge:
        return ''
    
    # Remove common prefixes
    text = re.sub(r'^(New Charge:|Weekender:|Charge Description:)\s*', '', raw_charge, flags=re.IGNORECASE)
    
    # Extract the description part (between statute and parentheses)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback: if no statute pattern, try to get text before first parenthesis
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    
    return text.strip()


def scrape_hendry(max_pages=5, max_records=50):
    """
    Scrape Hendry County inmate roster.
    
    Args:
        max_pages: Maximum number of pages to scrape (default 5, set to 0 for all)
        max_records: Maximum total records to scrape (default 50, set to 0 for unlimited)
    """
    records = []
    
    # Get limits from environment or use defaults
    max_pages = int(os.getenv('HENDRY_MAX_PAGES', max_pages))
    max_records = int(os.getenv('HENDRY_MAX_RECORDS', max_records))
    
    try:
        co = ChromiumOptions()
        co.auto_port()
        co.set_argument('--ignore-certificate-errors')
        
        page = ChromiumPage(co)
        
        def handle_cloudflare(page, max_wait=20):
            """Wait for Cloudflare challenge to clear."""
            sys.stderr.write("Checking for Cloudflare...\n")
            start = time.time()
            while time.time() - start < max_wait:
                title = page.title.lower()
                if "just a moment" not in title and "security challenge" not in title:
                    sys.stderr.write("Cloudflare cleared.\n")
                    return True
                time.sleep(1)
            return False
        
        # Navigate to roster page
        url = 'https://www.hendrysheriff.org/inmateSearch'
        sys.stderr.write(f"Navigating to {url}\n")
        sys.stderr.flush()
        
        try:
            page.get(url, timeout=30)
            sys.stderr.write("Page loaded successfully\n")
        except Exception as e:
            sys.stderr.write(f"Error loading page: {e}\n")
            print(json.dumps([]))
            return
        
        handle_cloudflare(page)
        time.sleep(2)
        
        # Set sort order to newest first
        sys.stderr.write("Setting sort order to newest first...\n")
        try:
            sort_select = page.ele('css:select#sort', timeout=5)
            if sort_select:
                sort_select.select.by_value('dateDesc')
                sys.stderr.write("Sort order set to Date (Newest - Oldest)\n")
                time.sleep(2)
        except Exception as e:
            sys.stderr.write(f"Could not set sort order: {e}\n")
        
        current_page = 1
        
        while True:
            sys.stderr.write(f"\n--- Processing page {current_page} ---\n")
            sys.stderr.flush()
            
            # Wait for cards to load
            time.sleep(1.5)
            
            # Find all inmate cards on this page
            cards = page.eles('css:.chakra-card')
            sys.stderr.write(f"Found {len(cards)} inmate cards on page {current_page}\n")
            
            if len(cards) == 0:
                sys.stderr.write("No cards found, stopping.\n")
                break
            
            for i, card in enumerate(cards):
                if max_records > 0 and len(records) >= max_records:
                    sys.stderr.write(f"Reached max_records limit ({max_records}), stopping.\n")
                    break
                
                try:
                    data = {}
                    
                    # Get name from h2 header
                    name_elem = card.ele('tag:h2')
                    if name_elem:
                        full_name = name_elem.text.strip()
                        data['Full_Name'] = full_name
                        if ',' in full_name:
                            parts = full_name.split(',', 1)
                            data['Last_Name'] = parts[0].strip()
                            data['First_Name'] = parts[1].strip()
                    
                    # Get posted date (booking date)
                    date_elem = card.ele('css:.chakra-text')
                    if date_elem:
                        data['Booking_Date'] = date_elem.text.strip()
                    
                    # Get the detail link to extract inmate ID
                    detail_link = card.ele('css:a[href*="/inmateSearch/"]')
                    if detail_link:
                        href = detail_link.attr('href')
                        # Extract inmate ID from URL like /inmateSearch/52046517
                        match = re.search(r'/inmateSearch/(\d+)', href)
                        if match:
                            data['Inmate_ID'] = match.group(1)
                            # Build full URL only if href is relative
                            if href.startswith('http'):
                                data['Detail_URL'] = href
                            else:
                                data['Detail_URL'] = f"https://www.hendrysheriff.org{href}"
                    
                    # Get mugshot from img
                    img_elem = card.ele('css:.chakra-image')
                    if img_elem:
                        src = img_elem.attr('src')
                        if src and 'missing-image' not in src:
                            data['Mugshot_URL'] = src
                    
                    # Get text from render-html div for basic info
                    render_div = card.ele('css:.render-html')
                    if render_div:
                        card_text = render_div.text
                        
                        # Extract Inmate ID
                        id_match = re.search(r'Inmate ID:\s*(\S+)', card_text)
                        if id_match:
                            data['Booking_Number'] = id_match.group(1)
                        
                        # Extract Height
                        height_match = re.search(r'Height:\s*([^\n]+)', card_text)
                        if height_match:
                            data['Height'] = height_match.group(1).strip()
                        
                        # Extract Weight
                        weight_match = re.search(r'Weight:\s*([^\n]+)', card_text)
                        if weight_match:
                            val = weight_match.group(1).strip()
                            if 'Unavailable' not in val:
                                data['Weight'] = val
                        
                        # Extract Gender
                        gender_match = re.search(r'Gender:\s*([MF])', card_text)
                        if gender_match:
                            data['Sex'] = gender_match.group(1)
                        
                        # Extract Race
                        race_match = re.search(r'Race:\s*([A-Z])', card_text)
                        if race_match:
                            data['Race'] = race_match.group(1)
                        
                        # Extract Address
                        addr_match = re.search(r'Main Address:\s*\n?([^\n]+)', card_text)
                        if addr_match:
                            addr_val = addr_match.group(1).strip()
                            if 'Currently Unavailable' not in addr_val:
                                data['Address'] = addr_val
                    
                    # Only add if we have essential data
                    if data.get('Full_Name') and (data.get('Booking_Number') or data.get('Inmate_ID')):
                        # Use Inmate_ID as Booking_Number if not found
                        if not data.get('Booking_Number') and data.get('Inmate_ID'):
                            data['Booking_Number'] = f"HENDRY-{data['Inmate_ID']}"
                        
                        records.append(data)
                        sys.stderr.write(f"  [{len(records)}] {data.get('Full_Name', 'Unknown')}\n")
                    
                except Exception as e:
                    sys.stderr.write(f"  Error processing card {i+1}: {str(e)}\n")
                    continue
            
            # Check if we've hit our limits
            if max_records > 0 and len(records) >= max_records:
                break
            
            if max_pages > 0 and current_page >= max_pages:
                sys.stderr.write(f"Reached max_pages limit ({max_pages}), stopping.\n")
                break
            
            # Try to go to next page
            try:
                next_button = page.ele('css:button[aria-label="Page Right"]')
                if next_button:
                    # Check if we're on the last page
                    page_info = page.ele('css:button[aria-label*="Page"]')
                    if page_info:
                        page_text = page_info.text
                        # Parse "Page 1 of 58"
                        match = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', page_text)
                        if match:
                            current = int(match.group(1))
                            total = int(match.group(2))
                            if current >= total:
                                sys.stderr.write(f"Reached last page ({current} of {total})\n")
                                break
                    
                    next_button.click()
                    current_page += 1
                    time.sleep(2)
                else:
                    sys.stderr.write("No next button found, stopping.\n")
                    break
            except Exception as e:
                sys.stderr.write(f"Error navigating to next page: {e}\n")
                break
        
        page.quit()
        
    except Exception as e:
        sys.stderr.write(f"Fatal error: {str(e)}\n")
    
    sys.stderr.write(f"\nTotal records scraped: {len(records)}\n")
    print(json.dumps(records))


if __name__ == "__main__":
    scrape_hendry()
