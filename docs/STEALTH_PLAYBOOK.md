# 🥷 STEALTH_PLAYBOOK.md — Anti-Detection & Evasion Reference

> **The best scraper is the one the target never knows exists.**

This document consolidates all anti-bot evasion knowledge. Before fighting a Cloudflare block, read this first.

---

## Threat Model

### What We Face
| Anti-Bot System | Prevalence | Difficulty | Counties Using |
|---|---|---|---|
| **Cloudflare JS Challenge** | Common | 🟡 Medium | Sarasota, others |
| **Cloudflare Turnstile** | Growing | 🔴 Hard | Emerging threat |
| **Rate Limiting** | Universal | 🟢 Easy | All counties |
| **IP Blocking** | Common | 🟡 Medium | High-traffic counties |
| **User-Agent Filtering** | Common | 🟢 Easy | Most counties |
| **CAPTCHA (reCAPTCHA)** | Rare | 🔴 Hard | Broward, Miami-Dade |
| **ASP.NET ViewState** | Common | 🟡 Medium | Hillsborough, Seminole, Hernando |
| **Session/Cookie Validation** | Common | 🟡 Medium | Most dynamic sites |
| **Referer Checking** | Occasional | 🟢 Easy | Some counties |
| **JavaScript Rendering** | Common | 🟡 Medium | SPAs, React/Angular sites |

### What We Must Never Trigger
- Permanent IP ban (affects GitHub Actions shared runners)
- Abuse complaint to our ISP / hosting provider
- Legal notice from a county attorney
- Triggering "attack mode" on Cloudflare (blocks entire IP range)

---

## Evasion Techniques

### 1. DrissionPage Configuration (Primary)

DrissionPage is our primary tool because it uses a real Chromium browser, making it indistinguishable from a human user.

```python
from DrissionPage import ChromiumPage, ChromiumOptions

co = ChromiumOptions()
co.headless(False)                    # Headful is stealthier
co.set_argument('--no-sandbox')
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/122.0.0.0 Safari/537.36')

page = ChromiumPage(co)
```

**Key Settings:**
| Setting | Purpose | Value |
|---|---|---|
| `headless(False)` | Bypass headless detection | Use for Cloudflare-protected sites |
| `--disable-blink-features=AutomationControlled` | Remove automation flags | Always |
| `--no-sandbox` | Docker compatibility | Docker/CI only |
| Custom user-agent | Match real browser fingerprint | Rotate monthly |

### 2. Timing Patterns

**Never scrape with machine-like regularity.**

```python
import random, time

# Between page loads
time.sleep(random.uniform(2, 8))

# Between detail page clicks
time.sleep(random.uniform(1, 4))

# Between county runs
time.sleep(random.uniform(30, 120))
```

**Rules:**
- Minimum 2-second delay between any two requests to the same domain
- Add ±50% jitter to all delays (never exact same interval twice)
- Vary scrape start times (don't always run at :00 or :30)
- Space multiple counties at least 60 seconds apart

### 3. User-Agent Rotation

Maintain a pool of real, current user-agent strings:

```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Firefox/123.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
]

# Use a consistent UA per session (sites track UA changes mid-session)
selected_ua = random.choice(USER_AGENTS)
```

**Rules:**
- Update user-agent strings monthly (keep them current)
- Use the **same** UA for an entire scraping session (switching mid-session is suspicious)
- Include both Windows and Mac UAs (match the real world distribution)
- Never use obviously fake UAs or include "bot" in the string

### 4. Cookie & Session Management

```python
# Accept cookies — refusing cookies is suspicious
page.get('https://county-site.com')
time.sleep(2)

# Click "I Accept" if cookie banner appears
try:
    accept_btn = page.ele('xpath://button[contains(text(), "Accept")]')
    if accept_btn:
        accept_btn.click()
        time.sleep(1)
except:
    pass  # No cookie banner — that's fine
```

### 5. Referrer Chain
When navigating to detail pages, arrive from the list page (not directly):
```python
# Good: Navigate naturally
page.get('https://county-site.com/roster')  # Land on list first
time.sleep(random.uniform(2, 5))
page.ele('css:.detail-link').click()         # Then click to detail

# Bad: Jump directly to detail page
page.get('https://county-site.com/inmate/12345')  # Suspicious!
```

---

## Per-Platform Strategies

### SmartCOP / SmartWEB Systems
**Counties:** Bradford, DeSoto, Dixie, Escambia, Gadsden, Glades, Hamilton, Levy, Putnam, Santa Rosa, Sumter, Suwannee, Taylor

**Strategy:**
- Standard ASP.NET WebForms with ViewState
- Usually no Cloudflare protection
- Simple Puppeteer stealth is sufficient
- Clone the DeSoto script and swap the URL
- Watch for session timeout (refresh every 5 minutes)

```javascript
// SmartCOP pattern (Node.js)
const page = await browser.newPage();
await page.goto(SMARTCOP_URL, { waitUntil: 'networkidle2' });
// Wait for the jail roster table to load
await page.waitForSelector('.SmartWebTable');
const rows = await page.$$('.SmartWebTable tr');
```

### Tyler Tech / New World Systems
**Counties:** Flagler, Nassau, Walton

**Strategy:**
- Very slow page loads (10-30 seconds)
- DrissionPage required for JS rendering
- Increase all timeouts to 60s minimum
- Pagination via "Next" button click

```python
# Tyler Tech pattern
page.get(TYLER_URL)
page.wait.ele_loaded('css:.inmate-table', timeout=60)
```

### ASP.NET ViewState Applications
**Counties:** Hillsborough, Hernando, Seminole

**Strategy:**
- ViewState is a large hidden field that must be preserved
- DrissionPage handles this automatically (real browser)
- Do NOT try to re-implement ViewState with requests — use DP
- Watch for `__EVENTTARGET` and `__EVENTARGUMENT` in postbacks

### PHP / Simple HTML Sites
**Counties:** Citrus, Brevard, Charlotte (ColdFusion)

**Strategy:**
- Simplest targets — try `requests` + BeautifulSoup first
- Only escalate to DrissionPage if blocked
- These sites rarely change their layout

### PDF Rosters
**Counties:** Calhoun, Hardee

**Strategy:**
- Download PDF via `requests`
- Parse with `pdfplumber` (Python)
- Handle inconsistent formatting (columns shift between PDFs)
- Cache PDFs in `fixtures/` for regression testing

---

## Escalation Ladder

When a county blocks your scraper, escalate through these levels in order:

```
Level 1: Python requests + BeautifulSoup
    ↓ Blocked?
Level 2: Python requests + cloudscraper
    ↓ Blocked?
Level 3: DrissionPage (headless mode)
    ↓ Blocked?
Level 4: DrissionPage (headful mode)
    ↓ Blocked?
Level 5: DrissionPage (headful + longer delays + UA rotation)
    ↓ Blocked?
Level 6: Reduce frequency dramatically (every 4-6 hours)
    ↓ Still blocked?
Level 7: PAUSE county, investigate manually, consider proxy
```

**CRITICAL:** Never skip ahead. Always try the lightest approach first.

---

## Fingerprint Hygiene

### Browser Profile Isolation
- Each county run should use a **fresh** browser profile by default
- Do NOT share profiles across counties (cross-contamination risk)
- Clear cookies between runs unless session persistence is needed

### What NOT to Do
| Anti-Pattern | Why It's Bad |
|---|---|
| Disabling JavaScript | Sites detect this; marks you as bot |
| Using `requests` on Cloudflare sites | Immediate block |
| Same UA for months | Fingerprint goes stale, easier to flag |
| Exact 10-second intervals | Machine-like timing = instant detection |
| Requesting 100 pages/minute | Rate limit trigger |
| Ignoring `robots.txt` completely | May trigger abuse alerts |
| Parallel requests to same domain | Rate limit + detection trigger |
| Changing UA mid-session | Session tracking flags this |

---

## Quick Reference: County → Best Approach

| Anti-Bot Level | Strategy | Tool |
|---|---|---|
| **None** (simple HTML) | `requests` + BS4 | Fastest, least resource |
| **Basic** (UA check, rate limit) | `requests` + custom UA + delays | Low resource |
| **Medium** (Cloudflare JS challenge) | DrissionPage headless | Standard approach |
| **High** (Cloudflare strict/Turnstile) | DrissionPage headful | Most resource |
| **Extreme** (CAPTCHA required) | DrissionPage + CAPTCHA solver | Last resort |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
