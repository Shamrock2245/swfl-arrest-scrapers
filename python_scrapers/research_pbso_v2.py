from DrissionPage import ChromiumPage, ChromiumOptions
import time
from datetime import datetime, timedelta
import sys

def poc():
    co = ChromiumOptions()
    co.auto_port()
    co.headless(False)
    
    page = ChromiumPage(co)
    
    print("Navigating to PBSO...")
    page.get('https://www3.pbso.org/blotter/index.cfm')
    
    if not page.wait.ele_displayed('tag:body', timeout=15):
        print("Failed to load page")
        return

    print("Checking for hCaptcha frame...")
    # hCaptcha usually in an iframe
    if page.ele('tag:iframe[src*="hcaptcha.com"]'):
        print("hCaptcha detected. PLEASE SOLVE IT MANUALLY.")
        
        # Wait until the search button is enabled.
        # The script in pbso_dump.html says: $("#process").prop("disabled",false);
        # process is the submit button? No, id="process" is hidden. Submit button likely doesn't have an ID but is type submit.
        
        # Checking dump: Input: Name='None', ID='process', Type='submit'
        # Wait, the dump said Input: Name='process', ID='None', Type='hidden'
        # AND Input: Name='None', ID='process', Type='submit'
        # So the submit button has id='process'? Conflicting info in dump. 
        # Let's wait for the user to solve.
        
        time.sleep(10) # Give user time
        
    # Fill Dates
    # Default to yesterday for results
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
    print(f"Setting Start Date: {yesterday}")
    
    try:
        page.ele('#start_date').input(yesterday)
        # End date defaults to today?
        # page.ele('#end_date').input(yesterday)
    except Exception as e:
        print(f"Error setting date: {e}")

    # Click Submit/Search
    # Finding the button
    btns = page.eles('tag:button')
    submit_btn = None
    for b in btns:
        if 'search' in b.text.lower():
            submit_btn = b
            break
            
    if not submit_btn:
        # Try input type submit
        submit_btn = page.ele('css:input[type=submit]')
        
    if submit_btn:
        print("Clicking Search...")
        submit_btn.click()
        
        # Wait for result
        time.sleep(5)
        
        print(f"URL after search: {page.url}")
        
        # Check if it's a new page or same page
        if 'searchresults.cfm' in page.url:
            print("Successfully navigated to search results.")
            # Save results HTML
            with open('pbso_results_dump.html', 'w', encoding='utf-8') as f:
                f.write(page.html)
            print("Saved pbso_results_dump.html")
            
            # Print table info
            rows = page.eles('css:table tr')
            print(f"Found {len(rows)} rows in table.")
        else:
            print("Did not navigate to searchresults.cfm yet. Saving current HTML.")
            with open('pbso_fail_dump.html', 'w', encoding='utf-8') as f:
                f.write(page.html)
                
    else:
        print("Could not find submit button")

    page.quit()

if __name__ == "__main__":
    poc()
