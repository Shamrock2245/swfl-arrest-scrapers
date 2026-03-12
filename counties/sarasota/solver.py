#!/usr/bin/env python3
"""
Sarasota County Arrest Scraper using Scrapling and BeautifulSoup
Targets: https://cms.revize.com/revize/apps/sarasota/
Approach: Scrapling → date search form → detail pages → BeautifulSoup → JSON output
"""

import sys
import json
import time
import re
import datetime
import urllib.parse
from scrapling import Fetcher
from bs4 import BeautifulSoup


def clean_text(text):
    """Clean and normalize text."""
    if not text:
        return ""
    return " ".join(text.strip().split())


def clean_charge_text(raw_charge):
    """Clean charge text to extract human-readable description."""
    if not raw_charge:
        return ''
    text = re.sub(r'^(New Charge:|Weekender:)\s*', '', raw_charge, flags=re.IGNORECASE)
    match = re.search(r'[\d.]+[a-z]*\s*-\s*([^(]+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if '(' in text:
        description = text.split('(')[0].strip()
        description = re.sub(r'^[\d.]+[a-z]*\s*-\s*', '', description)
        return description.strip()
    return text.strip()


def extract_detail(html_content, url):
    """Parse detailed info from viewInmate.php OR booking.php"""
    data = {"Source": "Sarasota", "Scrape_Date": datetime.date.today().isoformat()}

    if url:
        data['URL'] = url
    data['County'] = 'Sarasota'
    data['State'] = 'FL'
    data['Scrape_Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        js_data = {}

        # 1. Name from h1.page-title
        h1 = soup.select_one('h1.page-title')
        if h1:
            name = h1.text.replace('Print', '').strip()
            js_data['Full_Name'] = name

        # 2. Personal info from div.text-right label → sibling div value
        for div in soup.select('div.text-right'):
            key = div.text.replace(':', '').strip()
            val_div = div.find_next_sibling('div')
            if val_div and key:
                val = val_div.text.strip()
                if val or key not in js_data:
                    js_data[key] = val

        # 3. Also check label → input pairs
        for label in soup.select('label'):
            key = label.text.replace(':', '').strip()
            parent = label.parent
            if parent:
                input_field = parent.select_one('input')
                if input_field and input_field.get('value'):
                    val = input_field['value'].strip()
                    if val or key not in js_data:
                        js_data[key] = val

        # 4. Charges from #data-table (viewInmate layout) OR div.offense (booking.php layout)
        charges = []
        table = soup.select_one('#data-table')
        if table:
            for row in table.select('tbody tr, tr'):
                cells = row.select('td')
                if len(cells) > 4:
                    charges.append({
                        'booking_num': cells[0].text.strip(),
                        'offense': cells[1].text.strip(),
                        'desc': cells[2].text.strip() if len(cells) > 2 else '',
                        'bond': cells[4].text.strip(),
                        'intake': cells[6].text.strip() if len(cells) > 6 else ''
                    })
        else:
            # booking.php layout
            for off_div in soup.select('div.offense'):
                charge_dict = {}
                for row in off_div.select('div.row'):
                    label_div = row.select_one('div.text-right')
                    val_div = label_div.find_next_sibling('div') if label_div else None
                    if label_div and val_div:
                        lbl = label_div.text.replace(':', '').strip()
                        val = val_div.text.strip()
                        charge_dict[lbl] = val
                
                intake_date = charge_dict.get('Arrest Date', '') or charge_dict.get('Date Arrested', '') or charge_dict.get('Booking Date', '') or charge_dict.get('Intake Date', '')
                charges.append({
                    'booking_num': js_data.get('Booking Number', ''),
                    'offense': charge_dict.get('Charge Description', ''),
                    'desc': '',
                    'bond': charge_dict.get('Bond Amount', ''),
                    'intake': intake_date
                })
                
        js_data['__CHARGES'] = charges

        # 5. Mugshot
        mug = soup.select_one('.mug img, img.mugshot, img[alt*="mugshot"]')
        if mug and mug.get('src'):
            js_data['__Mugshot'] = mug['src']
            
        sys.stderr.write(f"   🐛 DEBUG js_data keys: {list(js_data.keys())}\n")
        for dk in ['Booking Date', 'Date Arrested', 'Arrest Date', 'Arrested', 'Intake Date', 'Intake']:
            if dk in js_data:
                sys.stderr.write(f"   🐛 DEBUG {dk}: {js_data[dk]}\n")
            
        # ----------- Map JS fields → schema fields -----------
        field_map = {
            'DOB': 'DOB',
            'Date of Birth': 'DOB',
            'Race': 'Race',
            'Sex': 'Sex',
            'Gender': 'Sex',
            'Height': 'Height',
            'Weight': 'Weight',
            'Address': 'Address',
            'City': 'City',
            'State': 'State',
            'Zip Code': 'ZIP',
        }

        for js_key, py_key in field_map.items():
            if js_key in js_data:
                data[py_key] = clean_text(js_data[js_key])

        # Full Name
        if 'Full_Name' in js_data:
            data['Full_Name'] = clean_text(js_data['Full_Name'])
            if ',' in data['Full_Name']:
                parts = data['Full_Name'].split(',', 1)
                data['Last_Name'] = parts[0].strip()
                data['First_Name'] = parts[1].strip()

        # Arrest/Intake date from label fields
        for date_key in ['Booking Date', 'Date Arrested', 'Arrest Date', 'Arrested', 'Intake Date']:
            if date_key in js_data and clean_text(js_data[date_key]):
                data['Booking_Date'] = clean_text(js_data[date_key])
                break

        # Charges & Bond
        charges_list = []
        total_bond = 0.0
        for entry in js_data.get('__CHARGES', []):
            if not data.get('Booking_Number') and entry.get('booking_num'):
                data['Booking_Number'] = clean_text(entry['booking_num'])

            charge_desc = clean_charge_text(entry.get('offense', ''))
            if charge_desc:
                charges_list.append(charge_desc)

            # Bond
            bond_str = entry.get('bond', '0').replace('$', '').replace(',', '').strip()
            try:
                if bond_str:
                    total_bond += float(bond_str)
            except:
                pass

            # Intake date from charge row
            intake = clean_text(entry.get('intake', ''))
            if intake and not data.get('Booking_Date'):
                data['Booking_Date'] = intake

        if charges_list:
            data['Charges'] = " | ".join(charges_list)
        data['Bond_Amount'] = str(total_bond)

        # Mugshot
        if '__Mugshot' in js_data:
            data['Mugshot_URL'] = js_data['__Mugshot']

        # ZIP → Zipcode normalization
        if 'ZIP' in data:
            data['Zipcode'] = data.pop('ZIP')

    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error extracting detail: {e}\n")

    return data


def scrape_sarasota(days_back=7):
    """Main scraper: iterate dates → collect links → visit details → output JSON."""
    sys.stderr.write(f"🏖️ Sarasota County Scraper (Scrapling)\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")

    start_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    end_date = datetime.datetime.now()
    
    # Configure Scrapling fetcher
    fetcher = Fetcher()

    try:
        # Phase 1: Collect PINs and associated dates
        pin_to_dates = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%m/%d/%Y')
            sys.stderr.write(f"\n🔍 Searching date: {date_str}\n")
            
            page_num = 1
            while True:
                try:
                    search_url = f'https://cms.revize.com/revize/apps/sarasota/personSearch.php?type=date&date={date_str}'
                    if page_num > 1:
                        search_url += f'&page={page_num}'
                        
                    response = fetcher.get(search_url)
                    time.sleep(1)
                    
                    if response.status == 200:
                        soup = BeautifulSoup(response.html_content, 'html.parser')
                        pin_links = soup.select('a[href*="pinSearch.php"]')
                        
                        if not pin_links:
                            if page_num == 1:
                                sys.stderr.write(f"   📋 Found 0 inmates for {date_str}\n")
                            break
                            
                        # Extract PINs
                        new_pins = 0
                        for link in pin_links:
                            href = link.get('href', '')
                            if href and 'pin=' in href:
                                pin = href.split('pin=')[1].split('&')[0].strip().replace('%20', '')
                                if pin:
                                    if pin not in pin_to_dates:
                                        pin_to_dates[pin] = set()
                                        new_pins += 1
                                    pin_to_dates[pin].add(date_str)
                                    
                        sys.stderr.write(f"   📄 Page {page_num}: Found {new_pins} new PINs\n")
                        
                        # Check if there is a 'Next' pagination link
                        next_link = soup.select_one('a:-soup-contains("Next")')
                        if next_link and 'page=' in next_link.get('href', ''):
                            page_num += 1
                        else:
                            # Also check if any link exactly matches the next page number
                            page_links = soup.select(f'a[href*="&page={page_num + 1}"]')
                            if page_links:
                                page_num += 1
                            else:
                                break
                    else:
                        sys.stderr.write(f"   ⚠️ Bad status for {date_str} page {page_num}: {response.status}\n")
                        break
                except Exception as e:
                    import traceback
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.write(f"   ⚠️ Request failed for {date_str} page {page_num}: {e}\n")
                    break

            current_date += datetime.timedelta(days=1)
            time.sleep(1)

        sys.stderr.write(f"\n📊 Total unique PINs across {days_back} days: {len(pin_to_dates)}\n")

        if not pin_to_dates:
            sys.stderr.write("⚠️ No inmate links found.\n")
            return []

        # Phase 2: Resolve bookings for each PIN
        booking_urls = []
        for idx, (pin, target_dates) in enumerate(pin_to_dates.items()):
            sys.stderr.write(f"📝 [{idx+1}/{len(pin_to_dates)}] Resolving bookings for PIN: {pin}\n")
            try:
                pin_url = f"https://cms.revize.com/revize/apps/sarasota/pinSearch.php?pin={pin}"
                pin_resp = fetcher.get(pin_url)
                soup = BeautifulSoup(pin_resp.html_content, 'html.parser')
                
                # Check for bookings matching target dates
                for row in soup.select('tr.search-row'):
                    cells = row.select('td')
                    if len(cells) >= 3:
                        arrest_date = cells[0].text.strip()
                        if arrest_date in target_dates:
                            a_tag = cells[2].select_one('a')
                            if a_tag and a_tag.get('href'):
                                href = a_tag['href'].replace('%20', '').strip()
                                booking_urls.append(href)
                time.sleep(1)
            except Exception as e:
                sys.stderr.write(f"   ⚠️ Failed resolving PIN {pin}: {e}\n")
                
        # Remove duplicate booking urls if any
        booking_urls = list(set(booking_urls))
        base_url = "https://cms.revize.com/revize/apps/sarasota/"
        arrests = []
        # [PHASE 3] Fetch details for each booking URL
        print(f"\n📊 Total bookings to scrape: {len(booking_urls)}", file=sys.stderr)
        
        for idx, bkg_href in enumerate(booking_urls):
            detail_url = base_url + bkg_href
            sys.stderr.write(f"🔍 [{idx+1}/{len(booking_urls)}] {bkg_href.split('=')[1]}\n")
            try:
                # Use standard get for the final detail page
                res = fetcher.get(detail_url)
                
                # Check for rate limiting
                if res.status == 429:
                    sys.stderr.write("   ⚠️ Rate limited. Sleeping 60s...\n")
                    time.sleep(60)
                    res = fetcher.get(detail_url)
                
                # Parse detail page
                record = extract_detail(res.html_content, detail_url)
                if record:
                    # In booking.php, the booking number is often passed in the URL 
                    if not record.get('Booking_Number') and '=' in bkg_href:
                        record['Booking_Number'] = bkg_href.split('=')[1].strip()
                        
                    arrests.append(record)
                    sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")
            except Exception as e:
                sys.stderr.write(f"   ⚠️ Failed {detail_url}\n")
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stderr.write(f"   ⚠️ Failed scraping detail: {e}\n")
                
            time.sleep(1)

        return arrests

    except Exception as e:
        sys.stderr.write(f"❌ Scraper error: {e}\n")
        return []

def main():
    days_back = 1
    if len(sys.argv) > 1:
        try:
            days_back = int(sys.argv[1])
        except:
            pass

    sys.stderr.write(f"🚀 Starting Sarasota County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n\n")

    arrests = scrape_sarasota(days_back)
    print(json.dumps(arrests))
    return 0 if arrests else 1


if __name__ == "__main__":
    sys.exit(main())
