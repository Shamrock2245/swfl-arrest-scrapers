import os
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(True)
co.set_argument('--headless=new')
co.set_argument('--no-sandbox')
co.set_user_data_path(os.path.abspath('./tmp_userdata'))
page = ChromiumPage(co)
page.get('https://example.com')
print(page.title)
page.quit()
