import time
from scrapling import DynamicFetcher

fetcher = DynamicFetcher()

r1 = fetcher.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Index status: {r1.status}")

# POST to personSearch.php...
payload = {'type': 'date', 'date': '03/04/2026'}
r2 = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)
print(f"Search status: {r2.status}")

links = r2.css('a[href*="viewInmate.php"]')
print(f"Links found: {len(links)}")

if links:
    first_link = links[0].attrib.get('href')
    url = f"https://cms.revize.com/revize/apps/sarasota/{first_link.strip()}"
    print(f"\nDetail URL: {url}")
    
    r3 = fetcher.get(url)
    print(f"GET Status: {r3.status}")
    print(f"GET URL: {r3.url}")
    
    h1 = r3.css('h1.page-title')
    print("H1 Text:", getattr(h1[0], 'text', '') if h1 else 'None')
