import sys
import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--window-size=1920,1080'
        ]
    )
    
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
    )
    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    sys.stderr.write("Loading page...\n")
    page.goto('https://www.hendrysheriff.org/inmateSearch', wait_until="networkidle", timeout=60000)
    time.sleep(5)
    
    # Cloudflare check
    for attempt in range(10):
        if "just a moment" in page.title().lower():
            sys.stderr.write(f"Cloudflare check {attempt}...\n")
            time.sleep(3)
        else:
            break
            
    # scroll
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)
    
    html = page.content()
    with open('/Users/brendan/Desktop/shamrock-active-software/swfl-arrest-scrapers/python_scrapers/scrapers/hendry_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
        
    sys.stderr.write("Saved HTML to hendry_debug.html\n")
    browser.close()
