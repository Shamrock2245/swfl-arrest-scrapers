import time
from scrapling import Fetcher

fetcher = Fetcher()

print("1. GET index.php to init session...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')
# scrapling might return cookies in r1.cookies if using httpx? Or r1.request?
cookies = {}
if hasattr(r1, 'cookies'):
    cookies = dict(r1.cookies)
print("Cookies:", cookies)

print("\n2. POST to personSearch.php...")
payload = {'type': 'date', 'date': '2026-03-04'}
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload, cookies=cookies)
if hasattr(r2, 'cookies') and r2.cookies:
    cookies.update(dict(r2.cookies))
print("Cookies:", cookies)

# extract first link
links = r2.css('a[href*="viewInmate.php"]')
if not links:
    print("No links found")
else:
    first_link = links[0].attrib.get('href')
    url = f"https://cms.revize.com/revize/apps/sarasota/{first_link}"
    print(f"\n3. Detail URL: {url}")
    
    r3 = fetcher.get(url, cookies=cookies)
    print(f"GET Status: {r3.status}")
    print(f"GET URL: {r3.url}")
    
    # check if Name exists
    h1 = r3.css('h1.page-title')
    print("H1 Text:", getattr(h1[0], 'text', '') if h1 else 'None')
