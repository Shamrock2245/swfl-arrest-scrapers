
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

def diagnose():
    co = ChromiumOptions()
    co.auto_port() # Use a free port to avoid conflicts
    co.headless(False)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(co)
    
    try:
        url = 'https://cms.revize.com/revize/apps/sarasota/index.php'
        print(f"Navigating to {url}")
        page.get(url)
        
        # Cloudflare wait
        for i in range(20):
            if "Just a moment" not in page.title:
                break
            time.sleep(1)
            print("Waiting for Cloudflare...")
            
        print(f"Page Title: {page.title}")
        
        # Switch to Arrest Date tab
        tab = page.ele('text:Arrest Date')
        if tab:
            print("Found 'Arrest Date' tab, clicking...")
            tab.click()
            time.sleep(1)
        else:
            print("Could not find 'Arrest Date' tab")

        # Dump all inputs
        inputs = page.eles('tag:input')
        print(f"Found {len(inputs)} inputs:")
        for inp in inputs:
            print(f" - Tag: {inp.tag}, Name: {inp.attr('name')}, ID: {inp.attr('id')}, Class: {inp.attr('class')}, Placeholder: {inp.attr('placeholder')}")

        # Try to find the specific one
        date_input = page.ele('css:input[name="arrest_date"]')
        if date_input:
            print("✅ Found input with name='arrest_date'")
        else:
            print("❌ Did not find input with name='arrest_date'")
            
        # Save HTML for review
        with open('sarasota_diagnosis.html', 'w', encoding='utf-8') as f:
            f.write(page.html)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        page.quit()

if __name__ == "__main__":
    diagnose()
