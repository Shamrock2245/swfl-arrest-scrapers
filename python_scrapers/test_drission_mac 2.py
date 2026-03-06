import os
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(True)
co.set_argument('--headless=new')
co.set_argument('--no-sandbox')
co.set_browser_path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
co.set_user_data_path(os.path.abspath('./tmp_userdata_mac'))

try:
    page = ChromiumPage(co)
    page.get('https://example.com')
    print("Page title:", page.title)
    page.quit()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
