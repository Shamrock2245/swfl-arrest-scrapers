import sys
import re
from curl_cffi import requests
from bs4 import BeautifulSoup

def test_collier_postback():
    url = 'https://www2.colliersheriff.org/arrestsearch/Report.aspx'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    session = requests.Session()
    
    print("Sending initial GET...")
    resp1 = session.get(url, headers=headers, impersonate="chrome120")
    
    # Extract VIEWSTATE
    soup1 = BeautifulSoup(resp1.text, 'html.parser')
    viewstate = soup1.find('input', {'id': '__VIEWSTATE'})['value']
    viewstategen = soup1.find('input', {'id': '__VIEWSTATEGENERATOR'})['value']
    
    print(f"Extracted VIEWSTATE: {viewstate[:20]}...")
    
    # Send POST
    print("Sending AJAX POSTback for timerLoad...")
    post_headers = headers.copy()
    post_headers.update({
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-MicrosoftAjax': 'Delta=true',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www2.colliersheriff.org',
        'Referer': url
    })
    
    data = {
        'ScriptManager1': 'UpdatePanel1|timerLoad',
        '__EVENTTARGET': 'timerLoad',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategen,
        '__ASYNCPOST': 'true',
    }
    
    resp2 = session.post(url, headers=post_headers, data=data, impersonate="chrome120")
    
    print(f"Status: {resp2.status_code}")
    print(f"Response Preview:\n{resp2.text[:1500]}")
    
    with open('debug_postback.html', 'w') as f:
        f.write(resp2.text)

if __name__ == "__main__":
    test_collier_postback()
