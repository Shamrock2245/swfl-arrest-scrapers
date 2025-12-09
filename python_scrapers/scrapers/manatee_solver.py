#!/usr/bin/env python3
"""
Manatee County Arrest Scraper using DrissionPage
Bypasses Cloudflare/iframe security and extracts detailed arrest information
"""

import json
import sys
import time
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def scrape_manatee_arrests(search_date=None):
    """
    Scrape Manatee County arrests for a given date
    
    Args:
        search_date: Date string in MM/DD/YYYY format (defaults to today)
    
    Returns:
        List of arrest records as dictionaries
    """
    if not search_date:
        search_date = datetime.now().strftime("%m/%d/%Y")
    
    print(f"🚦 Starting Manatee County Scraper", file=sys.stderr)
    print(f"📅 Search Date: {search_date}", file=sys.stderr)
    
    # Configure browser with stealth settings
    co = ChromiumOptions()
    co.set_browser_path('/usr/bin/chromium-browser')
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    page = ChromiumPage(addr_or_opts=co)
    arrests = []
    
    try:
        # Navigate directly to the bookings iframe URL
        # The main page uses an iframe that loads from manatee-sheriff.revize.com/bookings
        url = "https://manatee-sheriff.revize.com/bookings"
        print(f"📡 Loading: {url}", file=sys.stderr)
        page.get(url)
        time.sleep(5)  # Wait for page and table to load
        
        print(f"🔍 Extracting booking numbers from results", file=sys.stderr)
        
        # Extract booking links from the table
        # Look for links that go to booking detail pages
        booking_links = page.eles('xpath://a[contains(@href, "/bookings/")]')
        
        # Filter out the main /bookings link (no ID)
        booking_links = [link for link in booking_links if link.attr('href') and not link.attr('href').endswith('/bookings') and not link.attr('href').endswith('/bookings/')]
        
        if not booking_links:
            print("ℹ️  No arrests found for this date", file=sys.stderr)
            return []
        
        print(f"📋 Found {len(booking_links)} booking records", file=sys.stderr)
        
        # Process each booking
        for idx, link in enumerate(booking_links[:50], 1):  # Limit to 50 for safety
            try:
                booking_number = link.text.strip()
                detail_url = link.attr('href')
                
                # Make URL absolute if needed
                if not detail_url.startswith('http'):
                    detail_url = f"https://www.manateesheriff.com{detail_url}"
                
                print(f"🔍 [{idx}/{len(booking_links)}] Processing: {booking_number}", file=sys.stderr)
                
                # Navigate to detail page
                page.get(detail_url)
                time.sleep(2)  # Human-like delay
                
                # Extract data from detail page
                record = extract_detail_data(page, booking_number, detail_url)
                
                if record:
                    arrests.append(record)
                    print(f"   ✅ {record.get('Full Name', 'Unknown')}", file=sys.stderr)
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️  Error processing {booking_number}: {e}", file=sys.stderr)
                continue
        
        print(f"\n✅ Successfully scraped {len(arrests)} arrests", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise
    
    finally:
        page.quit()
    
    return arrests

def extract_detail_data(page, booking_number, source_url):
    """
    Extract detailed arrest information from booking detail page
    
    Args:
        page: DrissionPage ChromiumPage object
        booking_number: Booking number string
        source_url: URL of the detail page
    
    Returns:
        Dictionary with arrest data
    """
    data = {
        'Booking Number': booking_number,
        'source_url': source_url
    }
    
    try:
        # Extract Personal Information section (two-column layout)
        # First Name, Last Name, Middle Name, DOB, Race, Gender, Hair, Eye, Height, Weight
        personal_fields = {
            'First Name': 'First Name',
            'Last Name': 'Last Name',
            'Middle Name': 'Middle Name',
            'Date of Birth': 'DOB',
            'Race': 'Race',
            'Gender': 'Sex',
            'Hair': 'Hair',
            'Eye': 'Eye',
            'Height': 'Height',
            'Weight': 'Weight'
        }
        
        for field_label, output_key in personal_fields.items():
            # Try to find the field by label
            field_elem = page.ele(f'xpath://text()[contains(., "{field_label}")]')
            if field_elem:
                # Get the parent element and find the input or value
                parent = field_elem.parent()
                value_elem = parent.ele('tag:input') or parent.next()
                if value_elem:
                    value = value_elem.attr('value') or value_elem.text
                    if value:
                        data[output_key] = clean_text(value)
        
        # Extract Bookings table data (Book #, Book Date, Released Date)
        booking_table = page.ele('xpath://table[.//th[contains(text(), "Book #")]]')
        if booking_table:
            rows = booking_table.eles('tag:tr')[1:]  # Skip header
            for row in rows:
                cells = row.eles('tag:td')
                if len(cells) >= 3:
                    book_num = clean_text(cells[0].text)
                    book_date = clean_text(cells[1].text)
                    released = clean_text(cells[2].text)
                    
                    if book_num:
                        data['Book Date'] = book_date
                        data['Released Date'] = released
        
        # Extract Charges table (Arrest Date, Statute, Desc., Sec. Desc., OBTS, Bond Amt.)
        charges_table = page.ele('xpath://table[.//th[contains(text(), "Arrest Date")] or .//th[contains(text(), "Statute")]]')
        charges_list = []
        bonds_list = []
        statutes_list = []
        arrest_dates = []
        
        if charges_table:
            rows = charges_table.eles('tag:tr')[1:]  # Skip header
            for row in rows:
                cells = row.eles('tag:td')
                if len(cells) >= 6:
                    arrest_date = clean_text(cells[0].text)
                    statute = clean_text(cells[1].text)
                    desc = clean_text(cells[2].text)
                    sec_desc = clean_text(cells[3].text)
                    obts = clean_text(cells[4].text)
                    bond_amt = clean_text(cells[5].text)
                    
                    if desc:
                        # Build full charge description
                        charge_text = desc
                        if statute:
                            charge_text = f"{statute} - {charge_text}"
                        if sec_desc and sec_desc != 'A/W':
                            charge_text = f"{charge_text} ({sec_desc})"
                        
                        charges_list.append(charge_text)
                        
                        if statute:
                            statutes_list.append(statute)
                        if bond_amt:
                            bonds_list.append(bond_amt)
                        if arrest_date:
                            arrest_dates.append(arrest_date)
        
        # Add aggregated charge data
        if charges_list:
            data['Charges'] = ' | '.join(charges_list)
            data['Charge 1'] = charges_list[0]
        
        if bonds_list:
            data['Bond Amount'] = bonds_list[0]
            data['Total Bond'] = sum(float(b.replace(',', '')) for b in bonds_list if b.replace(',', '').replace('.', '').isdigit())
        
        if statutes_list:
            data['Statute'] = ' | '.join(statutes_list)
        
        if arrest_dates:
            data['Arrest Date'] = arrest_dates[0]
        
        # Extract mugshot
        mugshot = page.ele('xpath://img[contains(@src, "photo") or contains(@src, "mugshot") or contains(@src, "image")]')
        if mugshot:
            mugshot_src = mugshot.attr('src')
            if mugshot_src and not mugshot_src.startswith('data:'):
                if not mugshot_src.startswith('http'):
                    mugshot_src = f"https://www.manateesheriff.com{mugshot_src}"
                data['Mugshot'] = mugshot_src
        
    except Exception as e:
        print(f"   ⚠️  Error extracting data: {e}", file=sys.stderr)
    
    return data

def main():
    """Main entry point"""
    # Get search date from command line or use today
    search_date = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        arrests = scrape_manatee_arrests(search_date)
        
        # Output as JSON
        print(json.dumps(arrests, indent=2))
        
        return 0 if arrests else 1
        
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
