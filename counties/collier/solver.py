import sys
import json
import re
from typing import List, Dict, Any
from curl_cffi import requests
from bs4 import BeautifulSoup

def scrape_county() -> None:
    url = 'https://www2.colliersheriff.org/arrestsearch/Report.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    records: List[Dict[str, Any]] = []
    
    try:
        session = requests.Session()
        
        # Step 1: Initial GET to fetch the form and VIEWSTATE
        resp1 = session.get(url, headers=headers, impersonate="chrome120", timeout=30)
        
        if resp1.status_code != 200:
            sys.stderr.write(f"❌ Error fetching initial page: status code {resp1.status_code}\n")
            print("[]")
            return
            
        soup1 = BeautifulSoup(resp1.text, 'html.parser')
        viewstate_elem = soup1.find('input', {'id': '__VIEWSTATE'})
        viewstategen_elem = soup1.find('input', {'id': '__VIEWSTATEGENERATOR'})
        
        if not viewstate_elem or not viewstategen_elem:
            sys.stderr.write("❌ Error: Could not find VIEWSTATE elements.\n")
            print("[]")
            return
            
        viewstate = viewstate_elem['value']
        viewstategen = viewstategen_elem['value']
        
        # Step 2: AJAX POST to simulate timer loading the grid
        post_headers = headers.copy()
        post_headers.update({
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-MicrosoftAjax': 'Delta=true',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www2.colliersheriff.org',
            'Referer': url
        })
        
        data = {
            'ScriptManager1': 'UpdatePanel1|timerLoad',
            '__EVENTTARGET': 'timerLoad',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstategen,
            '__ASYNCPOST': 'true',
        }
        
        response = session.post(url, headers=post_headers, data=data, impersonate="chrome120", timeout=30)
        
        if response.status_code != 200:
            sys.stderr.write(f"❌ Error during POSTback: status code {response.status_code}\n")
            print("[]")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table')
        
        name_table_indices = []
        
        # Pass 1: Find all tables that represent the start of an arrest record
        # These tables have exact headers: Name, Date of Birth, Residence
        for i, table in enumerate(tables):
            cells = [td.get_text(strip=True) for td in table.find_all('td')]
            if len(cells) == 6 and cells[0] == 'Name' and cells[1] == 'Date of Birth' and cells[2] == 'Residence':
                if ',' in cells[3]: # Format: LAST, FIRST
                    name_table_indices.append({
                        'index': i,
                        'name': cells[3],
                        'dob': cells[4],
                        'address': cells[5]
                    })
                    
        # Pass 2: For each name table, look ahead for the associated description and charges
        for name_data in name_table_indices:
            record = {
                "name": name_data['name'],
                "dob": name_data['dob'],
                "address": name_data['address'],
                "county": "Collier"
            }
            
            start_idx = name_data['index'] + 1
            end_idx = min(start_idx + 15, len(tables))
            
            charges_list = []
            
            for j in range(start_idx, end_idx):
                table = tables[j]
                cells = [td.get_text(strip=True) for td in table.find_all('td')]
                
                # Extract Description Data
                for k in range(len(cells) - 1):
                    label = cells[k]
                    value = cells[k+1]
                    
                    if label == 'A#' and value and len(value) > 3:
                        record['arrest_number'] = value
                    elif label == 'PIN' and value and len(value) > 3:
                        record['pin'] = value
                    elif label == 'Race' and value:
                        record['race'] = value
                    elif label == 'Sex' and value:
                        record['sex'] = value
                    elif label == 'Height' and value:
                        record['height'] = value
                    elif label == 'Weight' and value:
                        record['weight'] = value
                    elif label == 'Hair Color' and value:
                        record['hair_color'] = value
                    elif label == 'Eye Color' and value:
                        record['eye_color'] = value
                    elif label == 'Booking Date' and value:
                        record['booking_date'] = value
                    elif label == 'Booking Number' and value and len(value) > 5:
                        record['booking_number'] = value
                        record['id'] = value # use booking number as primary ID
                    elif label == 'Agency' and value:
                        record['agency'] = value
                    elif label == 'Age at Arrest' and value:
                        record['age'] = value
                        
                # Extract Charges Data
                if table.get('id') and 'gvCharge' in table.get('id'):
                    charge_rows = table.find_all('tr')[1:] # Skip header
                    for row in charge_rows:
                        row_cells = [td.get_text(strip=True) for td in row.find_all('td', recursive=False)]
                        if len(row_cells) >= 3:
                            offense = row_cells[2]
                            if offense and offense != '&nbsp;':
                                charges_list.append(offense)
                                
                # Bond Data
                bond_span = table.find('span', id=lambda x: x and 'lblBondSummary' in x)
                if bond_span:
                    bond_text = bond_span.get_text(strip=True)
                    if 'BONDED' in bond_text.upper():
                        record['bond_paid'] = 'BONDED'
                    elif bond_text and bond_text != 'No information available.':
                        record['bond_paid'] = bond_text
                    
                # Stop looking ahead if we grabbed the booking number and checked a few tables
                if 'booking_number' in record and j > start_idx + 5:
                    break
                    
            if charges_list:
                record['charges'] = ' | '.join(charges_list)
                
            # Grab mugshot if available
            # Note: order of mugshots generally matches order of records on this page
            all_mugshots = soup.select('img[src*="PicThumb"]')
            if len(all_mugshots) > len(records):
                img = all_mugshots[len(records)]
                if img and img.get('src'):
                    from urllib.parse import urljoin
                    record['mugshot_url'] = urljoin(url, img['src'])
            
            if 'booking_number' in record:
                records.append(record)
                
        # Return as JSON
        print(json.dumps(records))
        
    except Exception as e:
        sys.stderr.write(f"❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        print("[]")

if __name__ == "__main__":
    scrape_county()
