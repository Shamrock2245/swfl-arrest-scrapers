import os
import subprocess
import time
from bs4 import BeautifulSoup

print("Testing direct curl_cffi wrapper to fetch the Sarasota details page...")

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    print("curl_cffi not installed or broken")
    import sys
    sys.exit(1)

# We emulate a browser
session = curl_requests.Session(impersonate="chrome120")

print("Fetching index.php...")
r1 = session.get('https://cms.revize.com/revize/apps/sarasota/index.php')
print(f"Index Status: {r1.status_code}")

payload = {'type': 'name', 'lname': 'Smith', 'fname': ''}
print("Fetching personSearch.php...")
r2 = session.post('https://cms.revize.com/revize/apps/sarasota/personSearch.php', data=payload)
print(f"Search Status: {r2.status_code}")

soup = BeautifulSoup(r2.text, 'html.parser')
links = soup.select('a[href*="viewInmate.php"]')

if links:
    href = links[0].get('href')
    
    # Try exact URL
    url1 = f"https://cms.revize.com/revize/apps/sarasota/{href}"
    print(f"\n1. Trying exact URL: {url1}")
    r3 = session.get(url1, headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 1: {r3.status_code} URL: {r3.url}")
    
    # Try clean URL
    import urllib.parse
    parsed = urllib.parse.urlparse(href)
    qs = urllib.parse.parse_qs(parsed.query)
    clean_id = qs['id'][0].strip()
    url2 = f"https://cms.revize.com/revize/apps/sarasota/viewInmate.php?id={clean_id}"
    
    print(f"\n2. Trying clean URL: {url2}")
    r4 = session.get(url2, headers={"Referer": "https://cms.revize.com/revize/apps/sarasota/personSearch.php"})
    print(f"Status 2: {r4.status_code} URL: {r4.url}")
    
    soup2 = BeautifulSoup(r4.text, 'html.parser')
    h1 = soup2.select_one('h1.page-title')
    print("H1 Text:", h1.text if h1 else 'None')
