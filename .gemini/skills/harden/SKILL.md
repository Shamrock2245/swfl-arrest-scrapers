---
name: harden
description: Systematically strengthen scraper pipelines against network failures, anti-bot measures, data edge cases, and real-world brittleness that breaks idealized scraper designs.
---

# Harden — Production Scraper Resilience

## Overview
Scrapers face unique hardening challenges: county jail websites change layouts without warning, anti-bot systems block headless browsers, network timeouts occur mid-page-load, and data formats vary wildly between jurisdictions.

**Core principle:** Scrapers that only work with perfect conditions aren't production-ready. Harden against reality.

## Anti-Bot & Cloudflare Hardening

### DrissionPage (Python) Stack
```python
options = ChromiumOptions()
options.headless()
options.set_argument('--no-sandbox')
options.set_argument('--disable-dev-shm-usage')
options.set_argument('--disable-blink-features=AutomationControlled')
options.set_argument('--window-size=1920,1080')
options.set_user_agent('Mozilla/5.0 (X11; Linux x86_64) ...')

# Wait for Cloudflare challenge
for attempt in range(15):
    title = page.title or ''
    if 'just a moment' in title.lower():
        time.sleep(3)
    else:
        break
```

### curl_cffi (Python) Stack
```python
from curl_cffi import requests
session = requests.Session()
resp = session.get(url, impersonate="chrome120", timeout=30)
```

### Puppeteer (Node.js) Stack
```javascript
const browser = await puppeteer.launch({
  headless: 'new',
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
```

## Network Resilience

### Retry with Exponential Backoff
```python
import time

def fetch_with_retry(session, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait)
```

### Timeout Handling
- HTTP requests: 30s timeout
- Page loads (browser): 60s timeout
- Individual element waits: 10s timeout
- Total pipeline: 10min hard limit via GitHub Actions

## Data Edge Cases

### Name Parsing
```python
# Handle: "LAST, FIRST MIDDLE", "FIRST LAST", "LAST FIRST"
if "," in name:
    parts = name.split(",", 1)
    last = parts[0].strip()
    first = parts[1].strip()
else:
    tokens = name.split()
    first, last = tokens[0], tokens[-1]
```

### Bond Amount Cleaning
```python
import re
raw_bond = "$10,500.00"
cleaned = re.sub(r'[^\d.]', '', raw_bond)  # "10500.00"
```

### Date Format Normalization
```python
# County sites use: MM/DD/YYYY, M/D/YY, YYYY-MM-DD, "Jan 15, 2024"
from dateutil import parser
normalized = parser.parse(raw_date).strftime("%m/%d/%Y")
```

### Empty/Zero Records
- Zero records scraped → log warning, don't error
- All records are duplicates → log "0 new", still success
- Site is down → log error, exit gracefully, alert Slack

## ASP.NET WebForms Pattern
Many jail booking sites use ASP.NET. Key pattern:
```python
# 1. GET page → extract __VIEWSTATE, __EVENTVALIDATION
# 2. POST with form data + hidden fields
# 3. Parse response HTML table
viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
```

## Testing Strategies for Scrapers

### Pre-Deploy Verification
```bash
# Run solver standalone
python counties/{county}/solver.py --days-back 1
# Should output JSON array to stdout, logs to stderr
```

### Health Check Pattern
```python
records = scrape_fn(days_back=1)
if not isinstance(records, list):
    logger.error("Solver returned non-list")
    return None
logger.info(f"Scraped {len(records)} records")
```

## NEVER
- Assume a county website hasn't changed layout
- Skip retry logic for HTTP requests
- Trust that zero records means "no new arrests"
- Deploy without running solver standalone first
- Hard-code CSS selectors without fallback strategies
- Ignore Cloudflare/bot-detection responses
