# GitHub Gem Seeker: Stealthy Scraping Libraries for Florida Sheriff Arrest Scrapers

**Project:** `swfl-arrest-scrapers` — Shamrock Bail Bonds  
**Prepared:** March 4, 2026  
**Context:** Companion research to the 67-county Florida scraping strategy. Your current gold standard is the **Lee County GAS scraper** (Google Apps Script + UrlFetchApp). For Python-based counties you are using **DrissionPage** as the primary browser automation tool, with **Requests/BS4** for simple HTML sites and **pdfplumber** for PDF rosters.

---

## Executive Summary

Your existing DrissionPage strategy is solid — it sits at **11.5k GitHub stars** and is actively maintained. However, based on a review of your 67-county CSV and the specific site architectures you are targeting (SmartCOP/ASP.NET, Police-to-Citizen, New World/Tyler Tech, Cloudflare-protected portals, and plain HTML), there are **five high-priority gems** that directly address gaps in your current stack, plus three supporting tools worth knowing.

---

## The Five Priority Gems

### 1. Scrapling — `D4Vinci/Scrapling`

| Attribute | Value |
|-----------|-------|
| **GitHub** | https://github.com/D4Vinci/Scrapling |
| **Stars** | 22,000 (Excellent tier) |
| **Last Commit** | Last week (actively maintained) |
| **License** | BSD-3-Clause |
| **Install** | `pip install scrapling` |

**What it is.** Scrapling is the most complete all-in-one Python scraping framework currently available. It ships four fetcher classes under one import:

- `Fetcher` — fast HTTP requests with TLS/JA3 fingerprint impersonation (powered by `curl_cffi` under the hood)
- `StealthyFetcher` — headless browser with full fingerprint spoofing; bypasses Cloudflare Turnstile out of the box
- `DynamicFetcher` — full Playwright Chromium/Chrome browser automation for heavy JS sites
- `AsyncFetcher` / `AsyncStealthyFetcher` — async variants of the above

**Why it matters for your use case.** The majority of your "To Scrape" counties require DrissionPage precisely because they are JS-heavy or have anti-bot splash pages. Scrapling's `StealthyFetcher` handles those same scenarios and additionally solves Cloudflare (Broward County, Miami-Dade) without a separate captcha solver. Its **adaptive parser** is uniquely valuable: once you scrape an element with `auto_save=True`, the library remembers its location and can relocate it automatically if the page layout changes — critical for government sites that update their portals unpredictably.

**Fit to your county matrix:**

| County Type | Scrapling Class | Notes |
|-------------|-----------------|-------|
| SmartCOP (Bradford, DeSoto clone sites) | `Fetcher` | SmartCOP is ASP.NET but often responds to direct HTTP with proper TLS fingerprint |
| Cloudflare-protected (Broward, Miami-Dade) | `StealthyFetcher` | Bypasses CF Turnstile natively |
| JS-heavy portals (Orange, Hillsborough, Pinellas) | `DynamicFetcher` | Drop-in for your current DP usage |
| Simple HTML (Brevard, Citrus, Martin) | `Fetcher` | Faster than Requests + better stealth |

**Code pattern** (replaces your current Requests/BS4 calls):

```python
from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

# For simple HTML sites (Brevard, Citrus, Martin)
page = Fetcher.get('https://www.brevardsheriff.com/bookings/', stealthy_headers=True)
rows = page.css('table.bookings tr')

# For Cloudflare-protected sites (Broward, Miami-Dade)
page = StealthyFetcher.fetch('https://www.sheriff.org/DOD/Pages/ArrestSearch.aspx', headless=True)
records = page.css('.arrest-row', auto_save=True)

# For JS-heavy ASP.NET (Hillsborough, Orange, Pinellas)
page = DynamicFetcher.fetch('https://webapps.hcso.tampa.fl.us/ArrestInquiry', network_idle=True)
```

---

### 2. curl_cffi — `lexiforest/curl_cffi`

| Attribute | Value |
|-----------|-------|
| **GitHub** | https://github.com/lexiforest/curl_cffi |
| **Stars** | 5,100 (Solid tier) |
| **Last Commit** | Last week |
| **License** | MIT |
| **Install** | `pip install curl_cffi` |

**What it is.** A Python binding for `curl-impersonate` — a fork of libcurl that patches the TLS handshake to exactly match real browser fingerprints (Chrome, Firefox, Safari, Edge). It is the engine behind Scrapling's `Fetcher` class and behind the popular `Stealth-Requests` wrapper.

**Why it matters for your use case.** Many of your "Requests/BS4" counties (Baker/SmartCOP, Brevard, Citrus, Martin, Polk) are currently approached with standard `requests`, which produces a Python/urllib TLS fingerprint that some government WAFs flag. Swapping to `curl_cffi` is a **one-line change** that makes your HTTP requests indistinguishable from Chrome:

```python
from curl_cffi import requests

# Impersonate Chrome 131 — replaces your existing requests.get() calls
session = requests.Session(impersonate="chrome131")
resp = session.get('https://www.brevardsheriff.com/bookings/')
soup = BeautifulSoup(resp.text, 'lxml')
```

This is the lowest-friction upgrade available to your stack. It supports `chrome99` through `chrome131`, `firefox`, `safari`, and `edge`. It also supports HTTP/2 and HTTP/3 fingerprints, which are increasingly used by government portal CDNs.

---

### 3. Camoufox — `daijro/camoufox`

| Attribute | Value |
|-----------|-------|
| **GitHub** | https://github.com/daijro/camoufox |
| **Stars** | 5,800 (Solid tier) |
| **Last Commit** | Last week |
| **License** | MPL-2.0 |
| **Install** | `pip install camoufox && python -m camoufox fetch` |

**What it is.** A custom-compiled fork of Firefox with C++-level fingerprint spoofing. Unlike JavaScript-injection-based stealth tools, Camoufox patches the browser's C++ engine directly, making its fingerprint changes **undetectable through JavaScript inspection**. It is compatible with your existing Playwright code — you only change the browser initialization line.

**Why it matters for your use case.** Your most problematic counties are those with active bot detection: Duval (Jacksonville SO login), Pinellas (disclaimer + ASP.NET), Seminole (WebBond ASP.NET), and Hillsborough (heavy ASP.NET). These sites may fingerprint the browser at the WebGL, AudioContext, or WebRTC level — layers that JavaScript-patched Chrome tools cannot fully hide. Camoufox operates at the C++ level and spoofs all of these simultaneously.

It is particularly well-suited as a **Firefox-based alternative** to your DrissionPage (Chrome-based) scrapers. Running both Chrome (DrissionPage) and Firefox (Camoufox) scrapers means a site would need to block both browser fingerprint families to stop you.

```python
from camoufox.sync_api import Camoufox

with Camoufox(headless=True) as browser:
    page = browser.new_page()
    # Accept disclaimer — same Playwright API you already know
    page.goto('https://pcsoweb.com/InmateBooking')
    page.click('#disclaimer-accept')
    page.wait_for_load_state('networkidle')
    html = page.content()
```

---

### 4. Patchright — `Kaliiiiiiiiii-Vinyzu/patchright-python`

| Attribute | Value |
|-----------|-------|
| **GitHub** | https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python |
| **Stars** | 1,200 (Solid tier) |
| **Last Commit** | 2 weeks ago |
| **License** | Apache-2.0 |
| **Install** | `pip install patchright && patchright install chromium` |

**What it is.** A patched, undetected version of Playwright for Python. It is a **true drop-in replacement** — you change only the import line. Its core innovation is patching the `Runtime.enable` CDP leak, which is the single most common way anti-bot systems detect Playwright. It also removes `--enable-automation` flags and patches `navigator.webdriver`.

**Verified to pass:** Cloudflare, Kasada, Akamai, Shape/F5, DataDome, Fingerprint.com, CreepJS, Sannysoft, Incolumitas, BrowserScan, PixelScan.

**Why it matters for your use case.** If you are already comfortable with Playwright's API (your `osceola_solver.py` and `pinellas_solver.py` use it), Patchright is the most frictionless upgrade. Your existing Playwright scrapers become stealth scrapers with a single import swap:

```python
# Before:
from playwright.sync_api import sync_playwright

# After (zero other changes needed):
from patchright.sync_api import sync_playwright
```

This is the recommended upgrade path for your existing Playwright-based county scrapers (Osceola, Pinellas, Seminole, Orange).

---

### 5. nodriver — `ultrafunkamsterdam/nodriver`

| Attribute | Value |
|-----------|-------|
| **GitHub** | https://github.com/ultrafunkamsterdam/nodriver |
| **Stars** | 3,700 (Solid tier) |
| **Last Commit** | 4 months ago |
| **License** | AGPL-3.0 |
| **Install** | `pip install nodriver` |

**What it is.** The official successor to `undetected-chromedriver` (12.4k stars). It communicates with Chrome directly via the Chrome DevTools Protocol (CDP) without Selenium or WebDriver — eliminating the `navigator.webdriver` detection vector entirely. It is fully asynchronous and has a built-in `cf_verify()` method that can click Cloudflare "I'm not a robot" checkboxes automatically.

**Why it matters for your use case.** The `undetected-chromedriver` library (its predecessor) is the most battle-tested anti-detection Chrome tool in existence. `nodriver` inherits that reputation with a cleaner async API and no WebDriver dependency. It is the best choice for counties where you need to **interact with a real Chrome session** (Duval's login page, Broward's Cloudflare IUAM) without any WebDriver fingerprint.

```python
import asyncio
import nodriver as uc

async def scrape_broward():
    browser = await uc.start()
    page = await browser.get('https://www.sheriff.org/DOD/Pages/ArrestSearch.aspx')
    # Automatically handles Cloudflare challenges
    await page.cf_verify()
    await page.wait_for('table.results')
    html = await page.get_content()
    return html

asyncio.run(scrape_broward())
```

---

## Supporting Tools (Know These)

### undetected-chromedriver — `ultrafunkamsterdam/undetected-chromedriver`

| Stars | Last Commit | Status |
|-------|-------------|--------|
| 12,400 | Active | Predecessor to nodriver; still widely used |

The original and most-starred anti-detection Chrome tool. If you need Selenium compatibility (your existing Selenium scrapers), this is the direct upgrade. `nodriver` is preferred for new development, but `undetected-chromedriver` remains the most proven tool for legacy Selenium code.

### SeleniumBase — `seleniumbase/SeleniumBase`

| Stars | Last Commit | Status |
|-------|-------------|--------|
| 12,400 | Active | Excellent |

Ships two stealth modes: **UC Mode** (wraps `undetected-chromedriver`) and **CDP Mode** (direct CDP, similar to nodriver). Particularly useful for the ASP.NET ViewState counties (Hernando, Hillsborough, Seminole) because it has built-in form handling and wait utilities that simplify multi-step POST interactions.

### mechanize — `python-mechanize/mechanize`

| Stars | Last Commit | Status |
|-------|-------------|--------|
| 760 | Active | Niche but valuable |

The classic Python library for stateful HTTP form submission. It handles ASP.NET `__VIEWSTATE` and `__EVENTVALIDATION` fields automatically, making it the most efficient tool for SmartCOP sites that do not require JavaScript rendering. For the 14 SmartCOP counties in your CSV (Bradford, Dixie, Escambia, Gadsden, Glades, Hamilton, Putnam, Santa Rosa, Sumter, Suwannee, Taylor, etc.), a `mechanize` + `curl_cffi` combination may be faster and more reliable than a full browser.

---

## Recommended Stack by County Type

The following table maps each site architecture in your 67-county CSV to the optimal tool combination, ordered by priority.

| Site Architecture | Counties (Examples) | Primary Tool | Backup Tool | Notes |
|-------------------|---------------------|--------------|-------------|-------|
| **SmartCOP / ASP.NET (no JS required)** | Bradford, Dixie, Escambia, Gadsden, Glades, Hamilton, Putnam, Santa Rosa, Sumter, Suwannee, Taylor | `curl_cffi` + `mechanize` | `Scrapling Fetcher` | ViewState handled by mechanize; curl_cffi provides TLS stealth |
| **Simple HTML / PHP** | Brevard, Citrus, Holmes, Martin | `curl_cffi` + BS4 | `Scrapling Fetcher` | Drop-in for your current Requests/BS4 calls |
| **JS-heavy / ASP.NET (requires browser)** | Hillsborough, Orange, Pinellas, Seminole, Hernando | `Patchright` | `DrissionPage` (current) | Swap import; zero other changes |
| **Disclaimer / Accept button** | Collier, Flagler, Franklin, Nassau, Walton | `Patchright` or `Camoufox` | `DrissionPage` (current) | Both handle click-through disclaimers |
| **Cloudflare / Heavy Anti-Bot** | Broward, Miami-Dade | `Scrapling StealthyFetcher` | `nodriver` + `cf_verify()` | CF Turnstile bypass built-in |
| **Login Required** | Duval (Jacksonville SO) | `nodriver` | `Camoufox` | No WebDriver fingerprint; handles login flows |
| **Police-to-Citizen (P2C)** | Clay | `Patchright` | `nodriver` | P2C is Chromium-friendly |
| **New World / Tyler Tech** | Flagler, Nassau, Walton | `Patchright` | `DrissionPage` (current) | Slow-loading; Patchright's `wait_for_load_state` handles it |
| **PDF Roster** | Calhoun, Hardee | `pdfplumber` (current) | No change needed | Your current approach is correct |
| **GAS / Remote Trigger** | Lee | GAS (current) | No change needed | Your current approach is the gold standard |

---

## Migration Priority Order

Given your current working scrapers (Lee, Charlotte, DeSoto, Hendry, Sarasota, Manatee, Palm Beach), the recommended sequence for expanding coverage is:

1. **Immediate (this week):** Add `curl_cffi` to `requirements.txt` and swap all `requests.get()` calls in your Requests/BS4 scrapers (Brevard, Citrus, Martin, Holmes, Polk). This is a one-line change per file and immediately improves stealth for 5+ counties.

2. **Short-term (1–2 weeks):** Add `pip install patchright && patchright install chromium` and swap the import in your existing Playwright-based scrapers (Osceola, Pinellas, Seminole, Orange). Zero logic changes required.

3. **Medium-term (2–4 weeks):** Use `Scrapling StealthyFetcher` to tackle the Cloudflare counties (Broward, Miami-Dade). These have been "hard" precisely because standard browser automation is detected; Scrapling's CF bypass is the cleanest solution.

4. **SmartCOP batch (parallel):** Build one `curl_cffi` + `mechanize` template for the 14 SmartCOP counties. Your CSV already notes "CLONE YOUR DESOTO SCRIPT" for these — the same principle applies here. One template, 14 deployments.

---

## Star Count Summary Table

| Library | GitHub Repo | Stars | Tier | Best For Your Use Case |
|---------|-------------|-------|------|------------------------|
| **Scrapling** | D4Vinci/Scrapling | 22,000 | Excellent | All-in-one: CF bypass + adaptive parser + browser |
| **DrissionPage** *(current)* | g1879/DrissionPage | 11,500 | Excellent | JS-heavy sites; keep as primary browser tool |
| **undetected-chromedriver** | ultrafunkamsterdam/undetected-chromedriver | 12,400 | Excellent | Legacy Selenium; predecessor to nodriver |
| **SeleniumBase** | seleniumbase/SeleniumBase | 12,400 | Excellent | ASP.NET forms; UC Mode + CDP Mode |
| **curl_cffi** | lexiforest/curl_cffi | 5,100 | Solid | TLS fingerprint impersonation for HTTP requests |
| **Camoufox** | daijro/camoufox | 5,800 | Solid | Firefox-based; C++ level fingerprint spoofing |
| **nodriver** | ultrafunkamsterdam/nodriver | 3,700 | Solid | No WebDriver; CF verify; async Chrome |
| **Patchright** | Kaliiiiiiiiii-Vinyzu/patchright-python | 1,200 | Solid | Drop-in Playwright replacement; zero code changes |
| **mechanize** | python-mechanize/mechanize | 760 | Promising | ASP.NET ViewState; SmartCOP batch scraping |

---

## Open Source Credits

This research was powered by the following open source projects. If any of these help your operation, consider giving them a star on GitHub:

- **Scrapling** — https://github.com/D4Vinci/Scrapling ⭐
- **curl_cffi** — https://github.com/lexiforest/curl_cffi ⭐
- **Camoufox** — https://github.com/daijro/camoufox ⭐
- **Patchright** — https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python ⭐
- **nodriver** — https://github.com/ultrafunkamsterdam/nodriver ⭐
- **SeleniumBase** — https://github.com/seleniumbase/SeleniumBase ⭐
- **undetected-chromedriver** — https://github.com/ultrafunkamsterdam/undetected-chromedriver ⭐

---

*Report generated by the GitHub Gem Seeker skill for the `swfl-arrest-scrapers` project.*
