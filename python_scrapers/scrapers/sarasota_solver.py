#!/usr/bin/env python3
"""
Sarasota County Arrest Scraper using DrissionPage
Targets: https://cms.revize.com/revize/apps/sarasota/
Approach: DrissionPage browser → date search form → detail pages → JSON output
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
    """Configure and launch DrissionPage browser."""
    co = ChromiumOptions()
    co.auto_port()
    co.headless(False)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--window-size=1920,1080')
    co.set_user_agent(
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    return ChromiumPage(addr_or_opts=co)


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


def collect_inmates_by_date(page, arrest_date):
    """
    Submit the Sarasota date search form and collect detail URLs.
    Returns list of (inmate_id, detail_url) tuples.
    """
    base_url = "https://cms.revize.com/revize/apps/sarasota"
    search_url = f"{base_url}/personSearch.php"
    date_str = arrest_date.strftime('%Y-%m-%d')

    sys.stderr.write(f"\n🔍 Searching date: {date_str}\n")

    page.get(search_url)
    time.sleep(2)

    if not wait_for_cloudflare(page):
        sys.stderr.write("   ⚠️ Cloudflare blocked search page\n")
        return []

    # Fill in the date search form via JS
    found_links = page.run_js(f"""
        // Set the search type and date, then submit
        const form = document.querySelector('form');
        if (!form) return [];

        // Find date input and type selector
        const dateInput = document.querySelector('input[name="date"], input[type="date"]');
        const typeSelect = document.querySelector('select[name="type"]');

        if (typeSelect) {{
            for (let opt of typeSelect.options) {{
                if (opt.value === 'date') {{ opt.selected = true; break; }}
            }}
            typeSelect.dispatchEvent(new Event('change'));
        }}

        if (dateInput) {{
            dateInput.value = '{date_str}';
            dateInput.dispatchEvent(new Event('change'));
        }}

        // Submit form
        form.submit();
        return 'submitted';
    """)

    time.sleep(3)

    if not wait_for_cloudflare(page):
        sys.stderr.write("   ⚠️ Cloudflare blocked search results\n")
        return []

    # Extract links from search results
    links = page.run_js("""
        const results = [];
        document.querySelectorAll('a[href*="viewInmate.php"]').forEach(a => {
            const href = a.href || a.getAttribute('href');
            const text = a.textContent.trim();
            if (href) results.push({href: href, text: text});
        });
        return results;
    """)

    detail_urls = []
    if links:
        for link in links:
            href = link.get('href', '')
            if not href.startswith('http'):
                href = f"{base_url}/{href}"
            # Extract ID from URL
            import urllib.parse
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)
            inmate_id = qs.get('id', [''])[0]
            detail_urls.append((inmate_id, href))

    sys.stderr.write(f"   📋 Found {len(detail_urls)} inmates for {date_str}\n")
    return detail_urls


def extract_detail(page, inmate_id, detail_url):
    """
    Extract structured data from a Sarasota detail page using JavaScript.
    """
    data = {
        'Detail_URL': detail_url,
        'County': 'Sarasota',
        'State': 'FL',
        'Scrape_Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    try:
        page.get(detail_url)
        time.sleep(2)

        if not wait_for_cloudflare(page):
            sys.stderr.write("   ⚠️ Cloudflare on detail page\n")
            return data

        # Extract all data via JavaScript
        js_data = page.run_js("""
            const result = {};

            // 1. Name from h1.page-title
            const h1 = document.querySelector('h1.page-title');
            if (h1) {
                let name = h1.textContent.trim();
                // Remove "Print" button text if present
                name = name.replace(/Print.*$/i, '').trim();
                result['Full_Name'] = name;
            }

            // 2. Personal info from div.text-right label → sibling div value
            document.querySelectorAll('div.text-right').forEach(div => {
                const key = div.textContent.replace(':', '').trim();
                const valDiv = div.nextElementSibling;
                if (valDiv) {
                    const val = valDiv.textContent.trim();
                    if (key && val) result[key] = val;
                }
            });

            // 3. Also check label → input pairs
            document.querySelectorAll('label').forEach(label => {
                const key = label.textContent.replace(':', '').trim();
                const input = label.parentElement ? label.parentElement.querySelector('input') : null;
                if (input && input.value) result[key] = input.value.trim();
            });

            // 4. Charges from #data-table
            const charges = [];
            const table = document.querySelector('#data-table');
            if (table) {
                table.querySelectorAll('tbody tr, tr').forEach(row => {
                    const cells = row.querySelectorAll('td');
                    if (cells.length > 4) {
                        charges.push({
                            booking_num: cells[0].textContent.trim(),
                            offense: cells[1].textContent.trim(),
                            desc: cells.length > 2 ? cells[2].textContent.trim() : '',
                            bond: cells[4].textContent.trim(),
                            intake: cells.length > 6 ? cells[6].textContent.trim() : ''
                        });
                    }
                });
            }
            result['__CHARGES'] = charges;

            // 5. Mugshot
            const mugImg = document.querySelector('.mug img, img.mugshot, img[alt*="mugshot"]');
            if (mugImg && mugImg.src) result['__Mugshot'] = mugImg.src;

            return result;
        """)

        if not js_data:
            return data

        # Map JS fields → schema fields
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
        for date_key in ['Arrest Date', 'Arrested', 'Date Arrested', 'Intake Date']:
            if date_key in js_data:
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
    sys.stderr.write(f"🏖️ Sarasota County Scraper (DrissionPage)\n")
    sys.stderr.write(f"📅 Days back: {days_back}\n")

    start_date = datetime.datetime.now() - datetime.timedelta(days=days_back)
    end_date = datetime.datetime.now()
    page = setup_browser()

    try:
        # Phase 1: Collect all inmate links across date range
        all_links = []
        current_date = start_date
        while current_date <= end_date:
            links = collect_inmates_by_date(page, current_date)
            all_links.extend(links)
            current_date += datetime.timedelta(days=1)
            time.sleep(1)

        # Deduplicate by URL
        seen = set()
        unique_links = []
        for iid, url in all_links:
            if url not in seen:
                seen.add(url)
                unique_links.append((iid, url))

        sys.stderr.write(f"\n📊 Total unique inmates across {days_back} days: {len(unique_links)}\n")

        if not unique_links:
            sys.stderr.write("⚠️ No inmate links found.\n")
            return []

        # Phase 2: Visit each detail page
        arrests = []
        for idx, (iid, detail_url) in enumerate(unique_links, 1):
            sys.stderr.write(f"\n🔍 [{idx}/{len(unique_links)}] {iid or 'unknown'}\n")

            try:
                record = extract_detail(page, iid, detail_url)

                # Skip records without booking date
                if not record.get('Booking_Date'):
                    sys.stderr.write("   ⚠️ Missing Booking_Date, skipping\n")
                    continue

                if record.get('Full_Name') or record.get('Booking_Number'):
                    arrests.append(record)
                    sys.stderr.write(f"   ✅ {record.get('Full_Name', 'Unknown')}\n")
                else:
                    sys.stderr.write("   ⚠️ No name or booking number, skipping\n")

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
