#!/usr/bin/env python3
"""
Manatee County Arrest Scraper using DrissionPage
Bypasses Cloudflare/iframe security and extracts detailed arrest information
Now with pagination support for historical data collection
"""

import json
import sys
import time
from datetime import datetime, timedelta
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return " ".join(text.strip().split())

def scrape_manatee_arrests(days_back=21, max_pages=10):
    """
    Scrape Manatee County arrests with pagination support
    
    Args:
        days_back: Number of days to go back (default: 21 for 3 weeks)
        max_pages: Maximum number of pages to scrape (default: 10)
    
    Returns:
        List of arrest records as dictionaries
    """
    print(f"🚦 Starting Manatee County Scraper", file=sys.stderr)
    print(f"📅 Days back: {days_back}", file=sys.stderr)
    print(f"📄 Max pages: {max_pages}", file=sys.stderr)
    
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
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    try:
        # Navigate directly to the bookings iframe URL
        base_url = "https://manatee-sheriff.revize.com/bookings"
        
        # Pagination loop
        current_page = 1
        all_booking_links = []
        
        while current_page <= max_pages:
            print(f"\n📄 Processing page {current_page}...", file=sys.stderr)
            
            # Navigate to list page (with page parameter if not first page)
            if current_page == 1:
                url = base_url
            else:
                url = f"{base_url}?page={current_page}"
            
            print(f"📡 Loading: {url}", file=sys.stderr)
            page.get(url)
            time.sleep(5)  # Wait for page and table to load
            
            print(f"🔍 Extracting booking numbers from page {current_page}", file=sys.stderr)
            
            # Extract booking links from the table
            booking_links = page.eles('xpath://a[contains(@href, "/bookings/")]')
            
            # Filter out the main /bookings link (no ID)
            booking_links = [link for link in booking_links if link.attr('href') and not link.attr('href').endswith('/bookings') and not link.attr('href').endswith('/bookings/')]
            
            print(f"   📋 Found {len(booking_links)} inmates on page {current_page}", file=sys.stderr)
            
            if len(booking_links) == 0:
                print("   ⚠️  No inmates found on this page, stopping pagination", file=sys.stderr)
                break
            
            all_booking_links.extend(booking_links)
            
            # Check if there's a next page button
            # Look for pagination controls - common patterns: "Next", "›", page numbers
            next_button = page.ele('text:Next') or page.ele('css:.pagination .next') or page.ele('css:a[rel="next"]') or page.ele('xpath://a[contains(text(), "›")]')
            
            if not next_button or current_page >= max_pages:
                if current_page >= max_pages:
                    print(f"   ℹ️  Reached maximum pages ({max_pages})", file=sys.stderr)
                else:
                    print("   ℹ️  No more pages available", file=sys.stderr)
                break
            
            current_page += 1
            time.sleep(2)  # Be nice to the server
        
        print(f"\n📊 Total inmates found across {current_page} page(s): {len(all_booking_links)}", file=sys.stderr)
        
        # Process each booking
        stopped_early = False
        for idx, link in enumerate(all_booking_links, 1):
            try:
                booking_number = link.text.strip()
                detail_url = link.attr('href')
                
                # Make URL absolute if needed
                if not detail_url.startswith('http'):
                    detail_url = f"https://www.manateesheriff.com{detail_url}"
                
                print(f"\n🔍 [{idx}/{len(all_booking_links)}] Processing: {booking_number}", file=sys.stderr)
                
                # Navigate to detail page
                page.get(detail_url)
                time.sleep(2)  # Human-like delay
                
                # Extract data from detail page
                record = extract_detail_data(page, booking_number, detail_url)
                
                # Check date cutoff
                if record and 'Book Date' in record:
                    try:
                        book_date = datetime.strptime(record['Book Date'], '%m/%d/%Y')
                        if book_date < cutoff_date:
                            print(f"   ⏸️  Reached cutoff date ({book_date.strftime('%Y-%m-%d')}), stopping...", file=sys.stderr)
                            stopped_early = True
                            break
                    except:
                        pass  # Continue if date parsing fails
                
                if record:
                    arrests.append(record)
                    print(f"   ✅ {record.get('Full Name', 'Unknown')} (Total: {len(arrests)})", file=sys.stderr)
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ⚠️  Error processing {booking_number}: {e}", file=sys.stderr)
                continue
        
        print(f"\n📊 Total records collected: {len(arrests)}", file=sys.stderr)
        if stopped_early:
            print("ℹ️  Stopped early due to date cutoff", file=sys.stderr)
        
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
        
        # Build Full Name
        if 'First Name' in data and 'Last Name' in data:
            data['Full Name'] = f"{data['Last Name']}, {data['First Name']}"
        
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
            data['Total Bond'] = sum(float(b.replace(',', '').replace('$', '')) for b in bonds_list if b.replace(',', '').replace('$', '').replace('.', '').isdigit())
        
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
    # Parse command line arguments
    days_back = 21  # Default 3 weeks
    max_pages = 10  # Default 10 pages
    
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass
    
    try:
        arrests = scrape_manatee_arrests(days_back, max_pages)
        
        # Output as JSON
        print(json.dumps(arrests, indent=2))
        
        return 0 if arrests else 1
        
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
