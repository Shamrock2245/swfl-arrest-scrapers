# 🥷 SCRAPING_RULES — How We Scrape, Legally & Ethically

> **The best scraper is the one the target never notices.**

---

## Legal Foundation

### What We Scrape
✅ **Publicly accessible** arrest records from county sheriff/jail websites
✅ Data available to any person visiting the site with a standard web browser
✅ Only data covered under Florida Public Records Law (F.S. §119.01)

### What We Do NOT Do
❌ Bypass login walls or authentication systems
❌ Crack CAPTCHAs as primary defense (flag and skip instead)
❌ Access admin panels, APIs requiring keys we don't own, or restricted areas
❌ Violate `robots.txt` directives without investigation
❌ Impersonate law enforcement or government officials
❌ Exceed reasonable request rates (see Rate Limits below)

### If a County Contacts Us
1. **Immediately pause** the county scraper
2. **Cooperate** — provide information about our data use (public records for bail bond services)
3. **Notify** Brendan via Slack `#scraper-alerts`
4. **Do NOT resume** without explicit human authorization
5. **Document** in `LOGBOOK.md`

---

## Rate Limits (Non-Negotiable)

| Rule | Limit | Rationale |
|------|-------|-----------|
| Minimum delay between requests (same domain) | **2 seconds** | Prevent triggering rate limiters |
| Jitter on all delays | **±50%** | Appear human, not robotic |
| Maximum requests per minute (same domain) | **20** | Well below abuse thresholds |
| Maximum concurrent counties scraping | **5** | Prevent shared runner resource contention |
| Retry limit before pause | **3 consecutive failures** | Don't hammer a struggling site |
| Backoff on 429 response | **60 seconds minimum** | Respect the server's request |
| Scrape window | **Staggered cron, not :00/:30** | Avoid peak-time detection |

### Timing Patterns
```python
import random, time

# Between page loads — NEVER exact same interval
time.sleep(random.uniform(2, 8))

# Between detail page clicks
time.sleep(random.uniform(1, 4))

# Between county runs (if sequential)
time.sleep(random.uniform(30, 120))
```

---

## Anti-Detection Strategy

### Escalation Ladder
When a county blocks your scraper, escalate through these levels IN ORDER:

```
Level 1: Python requests + BeautifulSoup (lightest footprint)
    ↓ Blocked?
Level 2: requests + cloudscraper (Cloudflare JS challenge bypass)
    ↓ Blocked?
Level 3: DrissionPage headless (real Chromium fingerprint)
    ↓ Blocked?
Level 4: DrissionPage headful (most human-like)
    ↓ Blocked?
Level 5: DrissionPage headful + longer delays (10-15s) + UA rotation
    ↓ Blocked?
Level 6: Reduce frequency dramatically (every 4-6 hours)
    ↓ Still blocked?
Level 7: PAUSE county → investigate manually → consider proxy
```

**CRITICAL**: Never skip levels. Always try the lightest approach first.

### DrissionPage Configuration
```python
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(True)                     # Start headless, switch to headful if blocked
co.set_argument('--no-sandbox')
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36')
page = ChromiumPage(co)
```

### User-Agent Rotation
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
]
# Use SAME UA for entire session — switching mid-session is suspicious
selected_ua = random.choice(USER_AGENTS)
```

**Update UAs monthly**. Stale user-agents are easy to fingerprint.

---

## Per-Platform Strategies

### SmartCOP / SmartWEB (13 counties)
- No anti-bot protection typically
- Standard Puppeteer/DrissionPage works
- Clone DeSoto script and swap URL
- Watch for session timeout (~5 min)

### ASP.NET ViewState (Hillsborough, Seminole, Hernando)
- ViewState is a large hidden field — let the real browser handle it
- DrissionPage handles this automatically
- Do NOT try to reimplement ViewState with `requests`

### Cloudflare-Protected (Sarasota + others)
- DrissionPage headful mode (preferred)
- Add 5-15s delays between requests
- Vary scrape start times
- If strict mode: consider reducing frequency

### Simple HTML / PHP (Brevard, Citrus)
- Use `requests` + BeautifulSoup — fastest and lightest
- No browser overhead needed
- These sites rarely change layout

### PDF Rosters (Calhoun, Hardee)
- Download PDF via `requests`
- Parse with `pdfplumber`
- Cache PDFs in `fixtures/` for regression

---

## Fingerprint Hygiene

### DO
- ✅ Use a fresh browser profile for each county run
- ✅ Accept cookies (refusing is suspicious)
- ✅ Navigate naturally (list page → detail page, not direct detail URLs)
- ✅ Maintain consistent UA for the entire session
- ✅ Include standard headers (Accept, Accept-Language, Accept-Encoding)

### DON'T
- ❌ Disable JavaScript (sites detect this)
- ❌ Use `requests` on Cloudflare-protected sites (instant block)
- ❌ Request 100+ pages per minute from any domain
- ❌ Use the same UA for months without updating
- ❌ Make parallel requests to the same domain
- ❌ Change UA mid-session

---

## What Triggers Detection

| Behavior | Risk Level | Fix |
|----------|-----------|-----|
| Exact-interval requests (every 30.0s) | 🔴 High | Add random jitter |
| Missing cookies/referrer | 🟡 Medium | Use real browser or set headers |
| Headless Chromium fingerprint | 🟡 Medium | DrissionPage stealth flags |
| High request rate (>30/min) | 🔴 High | Add delays |
| Accessing deep pages without visiting index | 🟡 Medium | Navigate naturally |
| Outdated user-agent string | 🟢 Low | Update monthly |
