import time
from scrapling import Fetcher

fetcher = Fetcher()

print("Fetching index.php...")
r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Status: {r1.status}")

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
print("\nFetching personSearch.php...")
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)
print(f"Status: {r2.status}")

links = r2.css('a[href*="viewInmate.php"]')
print(f"Links found: {len(links)}")

if links:
    url = f"https://cms.revize.com/revize/apps/sarasota/{links[0].attrib.get('href').strip()}"
    print(f"\nDetail URL: {url}")
    
    r3 = fetcher.get(url, extra_headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status: {r3.status}")
    print(getattr(r3.css('title')[0], 'text', '') if r3.css('title') else 'No title')
