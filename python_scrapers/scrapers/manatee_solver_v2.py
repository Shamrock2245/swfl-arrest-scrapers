#!/usr/bin/env python3
"""
Manatee County Arrest Scraper (Python/DrissionPage)
Scrapes arrest data from https://manatee-sheriff.revize.com/bookings
"""

import sys
import time
import json
import re
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def scrape_manatee(limit=None):
    """
    Scrape Manatee County arrests
    
    Args:
        limit: Maximum number of bookings to process (None for all)
    
    Returns:
        List of arrest dictionaries
    """
    
    print(f"🚦 Starting Manatee County Scraper", file=sys.stderr)
    if limit:
        print(f"📊 Limit: {limit} bookings", file=sys.stderr)
    
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
        # Navigate directly to the bookings page
        url = "https://manatee-sheriff.revize.com/bookings"
        print(f"📡 Loading: {url}", file=sys.stderr)
        page.get(url)
        
        # Wait for dynamic content to load
        print(f"⏳ Waiting for page to load...", file=sys.stderr)
        time.sleep(8)  # Give JavaScript time to populate the table
        
        # Extract all booking links using JavaScript evaluation
        print(f"🔍 Extracting booking links", file=sys.stderr)
        
        booking_urls = page.run_js("""
            const links = Array.from(document.querySelectorAll('a[href*="/bookings/"]'));
            const urls = new Set();
            
            links.forEach(link => {
                let href = link.getAttribute('href');
                if (!href) return;
                
                // Ignore links that are just /bookings (no ID)
                if (/\\/bookings\\/?$/i.test(href)) return;
                
                if (!href.startsWith('http')) {
                    href = 'https://manatee-sheriff.revize.com' + (href.startsWith('/') ? href : '/' + href);
                }
                urls.add(href);
            });
            
            return Array.from(urls);
        """)
        
        if not booking_urls:
            print("ℹ️  No booking links found", file=sys.stderr)
            return []
        
        print(f"📋 Found {len(booking_urls)} booking detail URLs", file=sys.stderr)
        
        # Apply limit if specified
        if limit:
            booking_urls = booking_urls[:limit]
            print(f"📊 Processing first {len(booking_urls)} bookings", file=sys.stderr)
        
        # Visit each detail page
        for idx, detail_url in enumerate(booking_urls, 1):
            print(f"🔍 [{idx}/{len(booking_urls)}] {detail_url}", file=sys.stderr)
            
            try:
                page.get(detail_url)
                time.sleep(2)
                
                # Extract data from detail page
                data = extract_detail_data(page, detail_url)
                
                if data and data.get('Booking Number'):
                    arrests.append(data)
                    name = data.get('Full Name', 'Unknown')
                    print(f"   ✅ {name}", file=sys.stderr)
                else:
                    print(f"   ⚠️  No valid data extracted", file=sys.stderr)
                    
            except Exception as e:
                print(f"   ❌ Error: {e}", file=sys.stderr)
                continue
        
        print(f"\n📊 Total arrests extracted: {len(arrests)}", file=sys.stderr)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
    finally:
        page.quit()
    
    return arrests

def extract_detail_data(page, source_url):
    """
    Extract detailed arrest information from booking detail page
    
    Args:
        page: DrissionPage ChromiumPage object
        source_url: URL of the detail page
    
    Returns:
        Dictionary with arrest data
    """
    data = {
        'source_url': source_url
    }
    
    try:
        # Extract booking number from URL
        booking_match = re.search(r'/bookings/(\d+)', source_url)
        if booking_match:
            data['Booking Number'] = booking_match.group(1)
        
        # Extract Personal Information fields
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
        
        # Use JavaScript to extract field values
        field_data = page.run_js("""
            const data = {};
            const labels = document.querySelectorAll('label, th, td, dt');
            
            labels.forEach(label => {
                const text = label.textContent.trim();
                let value = null;
                
                // Try to find the value in various ways
                const parent = label.parentElement;
                const nextSibling = label.nextElementSibling;
                const input = parent.querySelector('input');
                
                if (input) {
                    value = input.value || input.textContent;
                } else if (nextSibling) {
                    value = nextSibling.textContent || nextSibling.value;
                } else if (label.tagName === 'TD') {
                    const nextTd = label.nextElementSibling;
                    if (nextTd) value = nextTd.textContent;
                }
                
                if (value) {
                    data[text] = value.trim();
                }
            });
            
            return data;
        """)
        
        # Map extracted fields to our schema
        for field_label, output_key in personal_fields.items():
            if field_label in field_data:
                data[output_key] = clean_text(field_data[field_label])
        
        # Build full name if we have first/last
        if data.get('First Name') and data.get('Last Name'):
            middle = f" {data.get('Middle Name')}" if data.get('Middle Name') else ""
            data['Full Name'] = f"{data['Last Name']}, {data['First Name']}{middle}"
        
        # Extract booking and arrest dates
        if 'Book Date' in field_data:
            data['Book Date'] = clean_text(field_data['Book Date'])
        if 'Arrest Date' in field_data:
            data['Arrest Date'] = clean_text(field_data['Arrest Date'])
        if 'Released Date' in field_data:
            data['Released Date'] = clean_text(field_data['Released Date'])
        
        # Extract charges table
        charges_data = page.run_js("""
            const charges = [];
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.textContent.trim());
                
                // Look for charge table (has "Statute" or "Desc." headers)
                if (headers.some(h => h.includes('Statute') || h.includes('Desc'))) {
                    const rows = table.querySelectorAll('tbody tr, tr');
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 6) {
                            charges.push({
                                arrest_date: cells[0].textContent.trim(),
                                statute: cells[1].textContent.trim(),
                                desc: cells[2].textContent.trim(),
                                sec_desc: cells[3].textContent.trim(),
                                obts: cells[4].textContent.trim(),
                                bond_amt: cells[5].textContent.trim()
                            });
                        }
                    });
                }
            });
            
            return charges;
        """)
        
        if charges_data:
            charges_list = []
            bonds_list = []
            statutes_list = []
            
            for charge in charges_data:
                desc = charge.get('desc', '')
                statute = charge.get('statute', '')
                bond_amt = charge.get('bond_amt', '')
                
                if desc:
                    charge_text = desc
                    if statute:
                        charge_text = f"{statute} - {charge_text}"
                    charges_list.append(charge_text)
                    
                    if statute:
                        statutes_list.append(statute)
                    if bond_amt:
                        bonds_list.append(bond_amt)
            
            if charges_list:
                data['Charges'] = ' | '.join(charges_list)
                data['Charge 1'] = charges_list[0]
            
            if bonds_list:
                data['Bond Amount'] = bonds_list[0]
                # Calculate total bond
                total = 0
                for bond in bonds_list:
                    try:
                        amount = float(re.sub(r'[^0-9.]', '', bond))
                        total += amount
                    except:
                        pass
                if total > 0:
                    data['Total Bond'] = str(total)
            
            if statutes_list:
                data['Statute'] = ' | '.join(statutes_list)
        
        # Extract mugshot
        mugshot_url = page.run_js("""
            const img = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[src*="image"]');
            return img ? img.src : null;
        """)
        
        if mugshot_url and not mugshot_url.startswith('data:'):
            data['Mugshot'] = mugshot_url
        
    except Exception as e:
        print(f"   ⚠️  Error extracting data: {e}", file=sys.stderr)
    
    return data

if __name__ == "__main__":
    # Get limit from command line (default: 50 for testing)
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    arrests = scrape_manatee(limit=limit)
    print(json.dumps(arrests, indent=2))
