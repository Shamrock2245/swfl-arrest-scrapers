import os
import sys
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def test_collier():
    co = ChromiumOptions()
    co.headless(False)
    co.set_argument('--no-sandbox')
    co.set_argument('--window-size=1920,1080')
    co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    co.set_user_data_path(os.path.abspath('./tmp_userdata_mac_collier'))
    
    page = ChromiumPage(co)
    
    try:
        print("Navigating to Collier Sheriff's site...")
        page.get('https://ww2.colliersheriff.org/arrestsearch/Report.aspx')
        time.sleep(3)
        
        print("PAGE TITLE:", page.title)
        
        # Check for the expected tables
        tables = page.eles('tag:table')
        print(f"Found {len(tables)} tables on the page.")
        
        if tables:
            print("First table preview:")
            print(tables[0].html[:500])
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        page.quit()

if __name__ == "__main__":
    test_collier()
