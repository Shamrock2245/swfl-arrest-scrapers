import time
from scrapling import Fetcher

fetcher = Fetcher()

# 1. GET index.php to init session...
print("1. GET index.php to init session...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')
cookies = {}
if hasattr(r1, 'cookies'):
    cookies = dict(r1.cookies)
print("Cookies:", cookies)

# 2. POST to personSearch.php...
print("\n2. POST to personSearch.php...")
payload = {'type': 'date', 'date': '2026-03-04'}
headers = {
    'Referer': 'https://cms.revize.com/revize/apps/sarasota/index.php',
    'Origin': 'https://cms.revize.com'
}
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload, cookies=cookies, headers=headers)
if hasattr(r2, 'cookies') and r2.cookies:
    cookies.update(dict(r2.cookies))
print("Cookies:", cookies)

# extract first link
links = r2.css('a[href*="viewInmate.php"]')
if not links:
    print("No links found")
else:
    first_link = links[0].attrib.get('href')
    url = f"https://cms.revize.com/revize/apps/sarasota/{first_link.strip()}"
    print(f"\n3. Detail URL: {url}")
    
    headers['Referer'] = 'https://cms.revize.com/revize/apps/sarasota/index.php'
    r3 = fetcher.get(url, cookies=cookies, headers=headers)
    print(f"GET Status: {r3.status}")
    print(f"GET URL: {r3.url}")
    
    h1 = r3.css('h1.page-title')
    print("H1 Text:", getattr(h1[0], 'text', '') if h1 else 'None')
