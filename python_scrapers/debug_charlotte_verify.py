
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os

def get_input_val(page, label_text):
    try:
        # Try exact match first
        label = page.ele(f'text:^{label_text}$')
        if not label:
            # Try contains match
            label = page.ele(f'text:{label_text}')
        
        if label:
            # Get the next element which should be the input
            inp = label.next()
            if inp:
                if inp.tag == 'input':
                    return inp.value
                else:
                    return inp.text.strip()
    except Exception as e:
        print(f"Error getting {label_text}: {e}")
    return None

def debug_extraction():
    # The URL that caused the timeout/hang in the log (or just a sample)
    url = "https://inmates.charlottecountyfl.revize.com/bookings/202505884"
    
    co = ChromiumOptions()
    is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    co.headless(is_headless)
    co.auto_port()
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(co)
    print(f"Attempting to visit: {url}")
    page.get(url)
    
    time.sleep(5) # Allow full load
    
    print(f"Page Title: {page.title}")
    
    data = {}
    
    # Test Personal Info Extraction
    data['First_Name'] = get_input_val(page, 'First Name')
    data['Last_Name'] = get_input_val(page, 'Last Name')
    data['DOB'] = get_input_val(page, 'Date of Birth')
    data['Race'] = get_input_val(page, 'Race')
    data['Sex'] = get_input_val(page, 'Gender')
    data['Address'] = get_input_val(page, 'Address')
    
    print("\n--- Extracted Data ---")
    for k, v in data.items():
        print(f"{k}: {v}")
        
    # Check if we are finding the elements but they are empty
    if not data['First_Name']:
        print("\n❌ Failed to extract First Name. Dumping HTML around 'First Name'...")
        label = page.ele('text:First Name')
        if label:
            print(f"Label HTML: {label.html}")
            nxt = label.next()
            if nxt:
                print(f"Next HTML: {nxt.html}")
        else:
            print("Label 'First Name' NOT found.")

    page.quit()

if __name__ == "__main__":
    debug_extraction()
