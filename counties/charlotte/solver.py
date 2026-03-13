#!/usr/bin/env python3
"""
Charlotte County Arrest Scraper using DrissionPage
Targets: https://inmates.charlottecountyfl.revize.com/bookings
Approach: DrissionPage browser automation → listing page → detail pages → JSON output
Same Revize CMS as Manatee County
"""

import sys
import json
import time
import re
import datetime
from DrissionPage import ChromiumPage, ChromiumOptions


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


def setup_browser():
    """Configure and launch DrissionPage browser using shared core config."""
    from core.browser import create_browser
    return create_browser({"headless": True})


def wait_for_cloudflare(page, max_wait=20):
    """Wait for Cloudflare challenge to clear, if present."""
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ''
        if 'just a moment' not in title:
            return True
        sys.stderr.write(f"   ⏳ Cloudflare challenge... ({waited}/{max_wait}s)\n")
        time.sleep(1)
        waited += 1
    return False


def collect_booking_links(page, max_pages=10):
    """
    Phase 1: Collect all booking detail links from listing pages.
    Returns list of (booking_id, detail_url) tuples.
    """
    base_url = "https://inmates.charlottecountyfl.revize.com"
    all_links = []
    current_page = 1

    while current_page <= max_pages:
        url = f"{base_url}/bookings" if current_page == 1 else f"{base_url}/bookings?page={current_page}"
        sys.stderr.write(f"\n📄 Loading page {current_page}: {url}\n")

        page.get(url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write("   ❌ Cloudflare did not clear. Stopping.\n")
            break

        # Find booking links — /bookings/{id}
        booking_els = page.eles('xpath://a[contains(@href, "/bookings/")]')

        valid_links = []
        for el in booking_els:
            href = el.attr('href') or ''
            if href.endswith('/bookings') or href.endswith('/bookings/'):
                continue
            text = clean_text(el.text)
            if not href.startswith('http'):
                href = f"{base_url}{href}"
            # Extract booking ID from URL
            booking_id = href.split('/bookings/')[-1].split('?')[0].strip() if '/bookings/' in href else text
            valid_links.append((booking_id, href))

        sys.stderr.write(f"   📋 Found {len(valid_links)} inmates on page {current_page}\n")

        if not valid_links:
            sys.stderr.write("   ⚠️ No inmates found, stopping pagination\n")
            break

        all_links.extend(valid_links)

        # Check for next page
        next_btn = page.ele('css:a[rel="next"]') or page.ele('text:Next') or page.ele('css:.pagination .next a')
        if not next_btn or current_page >= max_pages:
            break

        current_page += 1
        time.sleep(1)

    # Deduplicate by URL
    seen = set()
    unique = []
    for bid, url in all_links:
        if url not in seen:
            seen.add(url)
            unique.append((bid, url))

    sys.stderr.write(f"\n📊 Total unique inmates: {len(unique)}\n")
    return unique


def extract_detail(page, booking_id, detail_url):
    """
    Phase 2: Extract structured data from a detail page using JavaScript.
    """
    data = {
        'Booking_Number': booking_id,
        'Detail_URL': detail_url,
        'County': 'Charlotte',
        'State': 'FL',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    try:
        page.get(detail_url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write("   ⚠️ Cloudflare on detail page\n")
            return data

        # Run JS to extract all data from the Revize detail page
        js_data = page.run_js("""
            const result = {};

            // 1. Personal Info — labels + inputs/siblings
            const labels = document.querySelectorAll('label, th, td, dt');
            labels.forEach(label => {
                const text = label.textContent.trim().replace(/:$/, '');
                let value = null;
                const parent = label.parentElement;
                const input = parent ? parent.querySelector('input') : null;
                const nextSib = label.nextElementSibling;
                if (input) value = input.value || input.textContent;
                else if (nextSib) value = nextSib.textContent || nextSib.value;
                if (value) result[text] = value.trim();
            });

            // 2. Booking table (#bookings-table)
            const bookTable = document.querySelector('#bookings-table');
            if (bookTable) {
                const row = bookTable.querySelector('tr[data-booking]');
                if (row) {
                    const cells = row.querySelectorAll('td');
                    if (cells.length >= 3) {
                        result['__Booking_Date'] = cells[2].textContent.trim();
                        if (cells.length > 3) result['__Status'] = cells[3].textContent.trim();
                    }
                }
            }

            // 3. Charges from .arrest-table (exclude mobile)
            const charges = [];
            document.querySelectorAll('table.arrest-table:not(.table-mobile)').forEach(table => {
                const headers = Array.from(table.querySelectorAll('th')).map(h => h.textContent.trim());
                if (headers.some(h => h.includes('Statute') || h.includes('Desc'))) {
                    table.querySelectorAll('tbody tr').forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 6) {
                            charges.push({
                                date: cells[0].textContent.trim(),
                                statute: cells[1].textContent.trim(),
                                desc: cells[2].textContent.trim(),
                                sec_desc: cells[3].textContent.trim(),
                                bond: cells[5].textContent.trim()
                            });
                        }
                    });
                }
            });
            result['__CHARGES'] = charges;

            // 4. Also look for ICE hold text
            result['__HAS_ICE'] = document.body.textContent.includes('ICE HOLD') ||
                                   document.body.textContent.includes('IMMIGRATION DETAINER');

            // 5. Mugshot
            const img = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[src*="image"]');
            if (img && !img.src.startsWith('data:')) result['__Mugshot'] = img.src;

            return result;
        """)

        if not js_data:
            return data

        # Map JS fields → schema fields
        field_map = {
            'First Name': 'First_Name',
            'Last Name': 'Last_Name',
            'Middle Name': 'Middle_Name',
            'Date of Birth': 'DOB',
            'Race': 'Race',
            'Gender': 'Sex',
            'Address': 'Address',
            'City': 'City',
            'State': 'State',
            'Zip Code': 'ZIP',
            'Height': 'Height',
            'Weight': 'Weight',
        }

        for js_key, py_key in field_map.items():
            if js_key in js_data:
                data[py_key] = clean_text(js_data[js_key])

        # Full Name
        if 'First_Name' in data and 'Last_Name' in data:
            data['Full_Name'] = f"{data['Last_Name']}, {data['First_Name']}"
            if data.get('Middle_Name'):
                data['Full_Name'] += f" {data['Middle_Name']}"

        # Booking Date
        if '__Booking_Date' in js_data:
            bd = clean_text(js_data['__Booking_Date'])
            if len(bd) > 5 and ('-' in bd or '/' in bd):
                data['Booking_Date'] = bd

        # Status
        if '__Status' in js_data:
            data['Status'] = clean_text(js_data['__Status'])

        # Charges & Bond
        charges_list = []
        total_bond = 0.0
        for entry in js_data.get('__CHARGES', []):
            desc = clean_text(entry.get('desc', ''))
            statute = clean_text(entry.get('statute', ''))
            sec_desc = clean_text(entry.get('sec_desc', ''))
            bond_str = clean_text(entry.get('bond', '0'))
            arr_date = clean_text(entry.get('date', ''))

            if 'Booking_Date' not in data and arr_date:
                data['Booking_Date'] = arr_date

            c_str = clean_charge_text(desc)
            if sec_desc and sec_desc != 'A/W':
                c_str += f" ({sec_desc})"
            if statute:
                c_str = f"{statute} - {c_str}"
            if c_str:
                charges_list.append(c_str)

            try:
                total_bond += float(bond_str.replace('$', '').replace(',', ''))
            except:
                pass

        # ICE Hold detection
        if js_data.get('__HAS_ICE'):
            charges_list.insert(0, "ICE HOLD")
            sys.stderr.write("   ⚠️ ICE/Federal Hold detected\n")

        if charges_list:
            data['Charges'] = " | ".join(charges_list)
        data['Bond_Amount'] = str(total_bond)

        # Mugshot
        if '__Mugshot' in js_data:
            data['Mugshot_URL'] = js_data['__Mugshot']

    except Exception as e:
        sys.stderr.write(f"   ⚠️ Error extracting detail: {e}\n")

    return data


def scrape_charlotte(days_back=21, max_pages=10):
    """Main scraper: collect links → visit details → filter by date → output JSON."""
    sys.stderr.write(f"🐊 Charlotte County Scraper (DrissionPage)\n")
    sys.stderr.write(f"📅 Days back: {days_back}  |  📄 Max pages: {max_pages}\n")

    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    page = setup_browser()

    try:
        booking_links = collect_booking_links(page, max_pages)

        if not booking_links:
            sys.stderr.write("⚠️ No booking links found.\n")
            return []

        arrests = []
        for idx, (booking_id, detail_url) in enumerate(booking_links, 1):
            sys.stderr.write(f"\n🔍 [{idx}/{len(booking_links)}] {booking_id}\n")

            try:
                record = extract_detail(page, booking_id, detail_url)

                # Date cutoff
                if record.get('Booking_Date'):
                    try:
                        for fmt in ['%m/%d/%Y', '%Y-%m-%d']:
                            try:
                                book_dt = datetime.datetime.strptime(record['Booking_Date'].split()[0], fmt)
                                if book_dt < cutoff_date:
                                    sys.stderr.write(f"   ⏸️ Past cutoff ({record['Booking_Date']}), stopping.\n")
                                    return arrests
                                break
                            except ValueError:
                                continue
                    except:
                        pass

                if record.get('Full_Name'):
                    arrests.append(record)
                    sys.stderr.write(f"   ✅ {record['Full_Name']}\n")
                else:
                    sys.stderr.write(f"   ⚠️ No name extracted, skipping\n")

            except Exception as e:
                sys.stderr.write(f"   ⚠️ Error: {e}\n")
                continue

            time.sleep(1)

        sys.stderr.write(f"\n📊 Total records: {len(arrests)}\n")
        return arrests

    except Exception as e:
        sys.stderr.write(f"❌ Fatal error: {e}\n")
        return []

    finally:
        try:
            page.quit()
        except:
            pass


def main():
    days_back = 21
    max_pages = 10
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

    sys.stderr.write(f"🚀 Starting Charlotte County scraper\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")
    sys.stderr.write(f"📄 Max pages: {max_pages}\n\n")

    arrests = scrape_charlotte(days_back, max_pages)
    print(json.dumps(arrests))
    return 0 if arrests else 1


if __name__ == "__main__":
    sys.exit(main())
