import time
from scrapling import Fetcher

fetcher = Fetcher()

# 1. Post to search
payload = {'type': 'date', 'date': '2026-03-04'}
response = fetcher.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)
print(f"POST URL: {response.url}")
print(f"POST Status: {response.status}")

# Try to extract the first viewInmate link
links = response.css('a[href*="viewInmate.php"]')
if not links:
    print("No links found")
else:
    first_link = links[0].attrib.get('href')
    url = f"https://cms.revize.com/revize/apps/sarasota/{first_link}"
    print(f"Detail URL: {url}")
    
    # 2. Get detail
    detail_resp = fetcher.get(url)
    print(f"GET URL: {detail_resp.url}")
    print(f"GET Status: {detail_resp.status}")
    print(f"Snippet: {detail_resp.body.decode('utf-8')[:200]}")
