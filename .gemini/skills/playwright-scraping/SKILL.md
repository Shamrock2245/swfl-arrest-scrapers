---
name: playwright-scraping
description: Use when building scrapers that need browser automation — Playwright or DrissionPage. Covers anti-bot evasion, Cloudflare bypass, headless Chrome, and browser-based data extraction.
source: Adapted from currents-dev/playwright-best-practices-skill (skills.sh #196, 26.7K installs)
---

# Playwright & Browser-Based Scraping

## Overview

Many Florida jail sites use modern web frameworks (React, Angular, ASP.NET) with
anti-bot protection. These require browser automation instead of simple HTTP requests.

## When to Use Browser Automation

| Signal | Use Browser? | Tool |
|--------|-------------|------|
| Full HTML in page source | ❌ No | `requests` + `BeautifulSoup` |
| XHR/fetch returning JSON | ❌ No | `requests` (hit API directly) |
| Blank HTML, JS renders data | ✅ Yes | `DrissionPage` or `Playwright` |
| Cloudflare "Just a moment..." | ✅ Yes | `DrissionPage` (preferred) |
| ASP.NET ViewState forms | ⚠️ Maybe | Try `curl_cffi` first, then browser |
| CAPTCHA on search | ⚠️ Evaluate | Browser + solver service (check ROI) |

## Our Two Browser Stacks

### DrissionPage (Preferred — Python)
Used by: Charlotte, DeSoto, Hendry, Highlands, Manatee, Orange, Polk, Sarasota

```python
from DrissionPage import ChromiumPage, ChromiumOptions

def setup_browser(headed=False):
    co = ChromiumOptions()
    co.auto_port()
    
    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        co.set_browser_path(chrome_path)
    
    if not headed:
        co.headless(True)
        co.set_argument('--headless=new')
    
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--window-size=1920,1080')
    co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36')
    
    return ChromiumPage(addr_or_opts=co)
```

### Playwright (Node.js / Python)
Used by: Osceola

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle')
```

## Anti-Bot Evasion Patterns

### 1. Cloudflare "Just a Moment" Challenge
```python
def wait_for_cloudflare(page, max_wait=30):
    """Wait for Cloudflare challenge to clear."""
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ''
        if 'just a moment' not in title and 'checking' not in title:
            return True
        time.sleep(1)
        waited += 1
    return False
```

### 2. Realistic User-Agent
Always set a current, realistic User-Agent. Never use Python default.
```python
co.set_user_agent(
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)
```

### 3. Rate Limiting
```python
time.sleep(1)  # 1 second between detail page requests
# For aggressive sites, use 2-3 seconds
```

### 4. Stealth Mode
DrissionPage's `--disable-blink-features=AutomationControlled` removes the
`navigator.webdriver` flag that sites check.

### 5. Session Persistence
Some sites set cookies on first visit. Keep the browser session alive:
```python
page = setup_browser()
try:
    page.get(search_url)  # First visit sets cookies
    wait_for_cloudflare(page)
    # Now navigate within the same session
    page.get(detail_url)
finally:
    page.quit()
```

## API Interception (Advanced)

Some SPAs expose internal APIs. DrissionPage can intercept XHR responses:
```python
# Listen for API calls
page.listen.start('api/inmates')
page.get(search_url)
# Wait for API response
packet = page.listen.wait()
data = packet.response.body  # JSON data!
```

This is how the Highlands solver works — far more reliable than DOM parsing.

## Docker / CI Setup

### Dockerfile requirements
```dockerfile
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_PATH=/usr/bin/chromium
ENV DISPLAY=:99
```

### GitHub Actions setup
```yaml
- uses: browser-actions/setup-chrome@latest
  with:
    chrome-version: stable
- run: pip install DrissionPage
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `WebDriverException: Chrome not found` | No Chromium installed | Set `CHROME_PATH` env var |
| `DevToolsActivePort file doesn't exist` | Docker /dev/shm too small | `--disable-dev-shm-usage` |
| `Element not found` | Page not fully loaded | Add explicit waits or `wait_for_cloudflare()` |
| Empty text from elements | Data loaded via JS after render | Wait for specific element, or intercept API |
| `net::ERR_CONNECTION_RESET` | Rate limited by server | Increase delays between requests |

## Best Practices

1. **Always wrap DrissionPage import in try/except** — CI may not have Chromium
2. **Use `page.quit()` in finally block** — Prevent zombie Chrome processes
3. **Log to stderr, not stdout** — stdout is reserved for JSON output
4. **Set reasonable timeouts** — 30s for page loads, 5s for element waits
5. **Reuse browser sessions** — Don't create new browser per detail page
