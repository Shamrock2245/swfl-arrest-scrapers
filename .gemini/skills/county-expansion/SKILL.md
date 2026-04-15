---
name: county-expansion
description: >
  Use this skill when expanding the scraper network to new Florida counties. Contains
  the 67-county expansion roadmap, prioritization framework, site reconnaissance procedure,
  and lead analysis strategy. The goal is total Florida coverage for maximum bail bond
  lead generation.
---

# County Expansion Playbook — Road to 67

## Mission
Expand from **18 active counties** to **all 67 Florida counties**. Every new county
directly increases Shamrock's geographic reach, lead volume, and revenue potential.
This isn't just scraping — it's market domination.

## Current Coverage Map

### ✅ Active (18 counties + Lee via GAS)
Brevard, Charlotte, Collier, DeSoto, Hendry, Highlands, Hillsborough,
Indian River, Lake, Lee*, Manatee, Martin, Orange, Osceola, Palm Beach,
Pinellas, Polk, Sarasota, Seminole

*Lee is scraped by GAS internal scraper (shamrock-bail-portal-site), not this repo.

### 🎯 Expansion Targets (49 remaining)

#### Tier 1 — High Priority (Pop >300K, high bond volume)
| County | Pop | Jail System | URL Pattern | Notes |
|--------|-----|-------------|-------------|-------|
| Miami-Dade | 2.7M | Miami-Dade Corrections | corrections.miamidade.gov | Largest county, complex system |
| Broward | 1.9M | BSO | sheriff.broward.org | 2nd largest, high volume |
| Duval | 1.0M | JSO | inmatesearch.jaxsheriff.org | Jacksonville metro |
| Pasco | 560K | PCSO | pascosheriff.com | Tampa metro spillover |
| Volusia | 550K | VCSO | volusia.org | Daytona Beach area |
| St. Lucie | 340K | SLCSO | stluciesheriff.com | Treasure Coast expansion |

#### Tier 2 — Medium Priority (Pop 100K-300K)
Escambia, Leon, Alachua, Marion, Okaloosa, Bay, St. Johns, Flagler,
Hernando, Citrus, Sumter, Putnam, Columbia, Nassau, Clay, Santa Rosa,
Walton, Osceola (done), Okeechobee, Glades

#### Tier 3 — Complete Coverage (Pop <100K)
Baker, Bradford, Calhoun, Dixie, Franklin, Gadsden, Gilchrist, Gulf,
Hamilton, Hardee, Holmes, Jackson, Jefferson, Lafayette, Levy, Liberty,
Madison, Monroe, Suwannee, Taylor, Union, Wakulla, Washington

## Site Reconnaissance Procedure

Before writing a single line of code, follow this recon checklist:

### Step 1: Find the Jail Roster
```bash
# Common URL patterns to try:
https://www.{county}sheriff.org/inmate-search
https://www.{county}so.org/inmates
https://jailviewer.{county}clerk.com
https://www.{county}jail.com
https://apps.{county}.org/inmatesearch
```

### Step 2: Determine Tech Stack
Open DevTools (Network tab) and classify:

| What You See | Stack | Tool to Use |
|-------------|-------|-------------|
| Full HTML in page source | Static | `requests` + `BeautifulSoup` |
| AJAX/XHR calls returning JSON | API-first | `requests` (direct API) |
| Blank HTML, JS loads data | React/Vue SPA | `DrissionPage` |
| ASP.NET ViewState, __EVENTVALIDATION | .NET PostBack | `curl_cffi` + state management |
| Cloudflare challenge page | CF Protected | `DrissionPage` (headless Chrome) |
| CAPTCHA on search | CAPTCHA | May need solver service — evaluate ROI |

### Step 3: Map the Data Flow
1. **Search page**: How to trigger a search (date range? last name? all?)
2. **Results page**: Where are the links to individual bookings?
3. **Detail page**: What fields are available? Map to our 39-column schema.
4. **Pagination**: How does the site paginate? Page numbers? Next buttons? Infinite scroll?

### Step 4: Check for API Shortcuts
Many jail systems use commercial software (JailTracker, Omnixx, Tyler Technologies)
that expose JSON APIs under the hood. Check:
- XHR requests in DevTools Network tab
- Common API endpoints: `/api/inmates`, `/api/search`, `/api/bookings`
- Hidden form actions that return JSON when `Accept: application/json` is sent

### Step 5: Test Anti-Bot Measures
```bash
curl -s -o /dev/null -w "%{http_code}" -H "User-Agent: Mozilla/5.0" "URL"
# 200 = open access
# 403 = bot detection (need browser or curl_cffi impersonation)
# 503 = Cloudflare challenge (need DrissionPage)
```

## Speed-Run New County (30-Minute Checklist)

For a site with no anti-bot and standard HTML:

```bash
# 1. Create county directory
COUNTY=duval
mkdir -p counties/$COUNTY
touch counties/$COUNTY/__init__.py
cp counties/_template/solver.py counties/$COUNTY/solver.py
cp counties/_template/runner.py counties/$COUNTY/runner.py  # if not already identical

# 2. Edit solver.py — update these 4 things:
#    - BASE_URL
#    - scrape_{county}() function name
#    - Page structure parsing
#    - Record field mapping

# 3. Create config
cp config/counties/_defaults.yaml config/counties/$COUNTY.yaml
# Edit: name, url, sheet_tab

# 4. Create workflow
cp .github/workflows/scrape_brevard.yml .github/workflows/scrape_$COUNTY.yml
# Edit: name, cron schedule (stagger!), county name

# 5. Test locally
python counties/$COUNTY/solver.py --days-back 3

# 6. Push and verify
git add -A && git commit -m "feat: add $COUNTY county scraper"
git push origin main
```

## Cron Schedule Staggering

Workflows must be staggered to avoid:
- IP rate limiting from jail sites
- GitHub Actions concurrency limits
- Overlapping Sheets writes

Pattern: Assign each county a unique (minute, hour-set) pair:
```
# Example: Every 6 hours, staggered by 5 minutes
County A: '0 */6 * * *'
County B: '5 */6 * * *'
County C: '10 */6 * * *'
...
```

## Lead Quality Analysis

Not all arrests are bail-bondable. After scraping, the pipeline should:

1. **Filter for bondable charges**: Misdemeanors with bond set > $0
2. **Score by bond amount**: Higher bond = higher premium = higher revenue
3. **Flag "hot" leads**: Recently booked + bond set + not yet bonded
4. **Geographic proximity**: Distance from Ft. Myers office matters for in-person bonds
5. **Repeat offenders**: Prior bookings indicate familiarity with bail process (easier close)

## Data Schema (39 columns)

The core record dict maps to Google Sheets columns via `core/writers/sheets_writer.py`:
```
Booking_Number, County, State, Facility, Full_Name, First_Name, Last_Name,
Middle_Name, DOB, Sex, Race, Height, Weight, Hair_Color, Eye_Color,
Address, City, Zipcode, Booking_Date, Release_Date, Status,
Charges, Bond_Amount, Bond_Type, Bond_Status, Agency, Case_Number,
Court_Date, Court_Type, Court_Location, Mugshot_URL, Detail_URL,
Scrape_Timestamp, Person_ID, Notes, Phone, Email, Emergency_Contact, Occupation
```

## Commercial Jail Software Patterns

Many Florida counties use the same commercial software. If you crack one, you crack many:

| Software | Counties Using It | API Pattern |
|----------|------------------|-------------|
| **JailTracker** (Lexis Nexis) | 15+ FL counties | REST API at `/inmate_details.aspx?id=` |
| **Omnixx/Tyler Odyssey** | 10+ FL counties | `.aspx` postback forms with ViewState |
| **Benchmark Analytics** | Several | JSON API at `/api/search` |
| **In-house** | Varies | Custom — must reverse-engineer per site |

## Known Gotchas

- `[2026-04-14]` DrissionPage requires Chromium — always wrap import in try/except
- `[2026-04-14]` SPA/React sites render data via JS — requests gets empty shells
- `[2026-04-14]` Some sites block headless Chrome UA — use realistic User-Agent strings
- `[2026-04-14]` Rate limiting: Add 0.5-1s delays between detail page fetches
- `[2026-04-14]` Always set `needs_xvfb: true` in workflow for browser-based scrapers
