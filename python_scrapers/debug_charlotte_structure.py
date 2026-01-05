
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os

def debug_structure():
    url = "https://inmates.charlottecountyfl.revize.com/bookings/202505884"
    
    co = ChromiumOptions()
    is_headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    co.headless(is_headless)
    co.auto_port()
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(co)
    print(f"Attempting to visit: {url}")
    page.get(url)
    
    time.sleep(5)
    
    print("Dumping simplified structure...")
    # Find anything that looks like a name or personal info
    
    # Check for h3/h1
    h1 = page.ele('tag:h1')
    if h1: print(f"H1: {h1.text}")
    
    # Check for labels
    labels = page.eles('text:First Name', timeout=2)
    print(f"Found {len(labels)} 'First Name' text elements")
    for l in labels:
        print(f" - Tag: {l.tag}, Parent: {l.parent().tag}, Next: {l.next().tag if l.next() else 'None'}")
        print(f"   HTML: {l.html}")

    # Check for dd/dt
    dts = page.eles('tag:dt')
    print(f"Found {len(dts)} DT elements")
    if dts:
        print(f"First DT: {dts[0].text}")

    page.quit()

if __name__ == "__main__":
    debug_structure()
