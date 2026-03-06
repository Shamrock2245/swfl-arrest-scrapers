import sys
from scrapling import Fetcher

def test_parse():
    try:
        page = Fetcher()
        # Fetching the main page to get one link
        list_response = page.get('https://inmates.charlottecountyfl.revize.com/bookings')
        links = list_response.css('a[href*="/bookings/"]')
        if not links:
            print("No links found on main page")
            return
            
        detail_href = links[0].attrib.get('href')
        detail_url = 'https://inmates.charlottecountyfl.revize.com' + detail_href if detail_href.startswith('/') else detail_href
        print(f"Testing with URL: {detail_url}")
        
        detail_response = page.get(detail_url)
        print(f"Detail Response Status: {getattr(detail_response, 'status', None)}")
        
        # Test finding fields
        print("\n--- Testing Data Extraction ---")
        
        # Try finding elements using CSS
        try:
            name_el = detail_response.css('.name, .inmate-name, h3.name, h1')
            print(f"Name elements found: {len(name_el)}")
                
            labels = detail_response.css('label')
            for label in labels[:2]:
                label_text = label.text if hasattr(label, 'text') else ''
                inp = label.xpath('./following-sibling::input')
                if inp:
                    print(f"  {label_text}: {inp[0].attrib.get('value', 'No Value')}")
                    
            # check bookings table
            tables = detail_response.css('table')
            print(f"Tables found: {len(tables)}")
            
            for table in tables:
                rows = table.css('tr')
                print(f" Table with {len(rows)} rows")
                if len(rows) > 0:
                    for j, row in enumerate(rows[:3]):
                        tds = row.css('td, th')
                        # Extract text from elements
                        td_texts = []
                        for td in tds:
                            # Using strip() if text exists
                            td_texts.append(td.text.strip() if hasattr(td, 'text') and td.text else '')
                        print(f"  Row {j}: {td_texts}")

            html_text = detail_response.html_content if hasattr(detail_response, 'html_content') else (detail_response.body.decode('utf-8') if hasattr(detail_response, 'body') else '')
            with open('test_booking_body.html', 'w') as f:
                f.write(html_text)
            print("Saved html_content to test_booking_body.html")
            
            import re
            mugshot_match = re.search(r'var\s+mugshotData\s*=\s*"([^"]+)"', html_text)
            if mugshot_match:
                mugshot_b64 = mugshot_match.group(1)
                print(f"Mugshot found (base64), length: {len(mugshot_b64)}, starts with: {mugshot_b64[:30]}...")
            else:
                print("Mugshot base64 not found via regex")
                    
        except Exception as sel_e:
            import traceback
            traceback.print_exc()
            print(f"Error testing selectors: {sel_e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_parse()
