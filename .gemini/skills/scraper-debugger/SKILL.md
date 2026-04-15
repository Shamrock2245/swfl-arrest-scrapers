---
name: scraper-debugger
description: >
  Use this skill when a scraper workflow is failing in GitHub Actions, when a solver
  is returning 0 records, or when debugging any runtime error in the scraping pipeline.
  Contains diagnostic procedures, common failure modes, and fix patterns.
---

# Scraper Debugger

This skill contains diagnostic procedures for debugging failing arrest scrapers.

## Diagnostic Procedure

When a scraper is failing, follow this checklist in order:

### Step 1: Identify the Failure
```bash
# Check recent workflow runs via GitHub API
curl -s "https://api.github.com/repos/Shamrock2245/swfl-arrest-scrapers/actions/runs?per_page=20" \
  | python3 -c "import json,sys; [print(f'{r[\"conclusion\"]:>10} | {r[\"name\"]:30} | {r[\"created_at\"]}') for r in json.load(sys.stdin)['workflow_runs']]"
```

### Step 2: Check the Solver Function Name
The universal runner looks for `scrape_{county_name}()` in `counties/{name}/solver.py`.
```bash
grep -n "def scrape" counties/{name}/solver.py
```
**The function name MUST match the folder name.**

### Step 3: Check the Solver Return Type  
The solver MUST `return` a list, not `print()` JSON.
```bash
grep -n "print\|return" counties/{name}/solver.py | tail -20
```

### Step 4: Check the Website
Verify the target website is still accessible and the HTML structure hasn't changed:
```bash
curl -s -o /dev/null -w "%{http_code}" "https://target-url.com"
```

### Step 5: Check for Argument Mismatches
If using an old-style runner (`python_scrapers/scrapers/run_*.py`), verify:
- The runner's subprocess call passes args the solver's argparse expects
- Named args (`--start`) vs positional args

### Step 6: Check for Missing Dependencies
```bash
pip list | grep -i "drissionpage\|playwright\|curl_cffi\|beautifulsoup4"
```

## Common Failure Modes

### 1. "No scrape function found"
**Cause**: Solver exports `scrape_county()` or `scrape()` instead of `scrape_{county_name}()`.
**Fix**: Rename the function to match the county directory name.

### 2. Runner returns None → sys.exit(1)
**Cause**: Solver raises an exception or returns None instead of a list.
**Fix**: Wrap solver in try/except that returns `[]` on failure.

### 3. "error: unrecognized arguments"
**Cause**: Old-style runner passes wrong argument format to solver's argparse.
**Fix**: Check solver's `argparse` and match the runner's subprocess call.

### 4. Detail pages return empty HTML
**Cause**: Website uses JavaScript rendering (React SPA). `requests` + BeautifulSoup gets an empty shell.
**Fix**: Either:
  - Extract data from the listing page (which is server-rendered)
  - Use DrissionPage or Playwright for browser-based scraping

### 5. Cloudflare challenge blocks scraper
**Cause**: Bot detection on target site. `requests` gets a 403 or challenge page.
**Fix**: Use `curl_cffi` (with impersonate) or DrissionPage (full browser).

### 6. DrissionPage/Chromium not available
**Cause**: Chromium binary not installed on runner (common on minimal Docker/CI images).
**Fix**: Add `google-chrome-stable` to the runner setup, or wrap import in try/except.

### 7. Google Sheets write fails
**Cause**: Service account credentials missing or expired.
**Fix**: Check `GOOGLE_SERVICE_ACCOUNT_KEY_PATH` env var and `creds/service-account-key.json` file.

## Environment Variables
```
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=creds/service-account-key.json
SLACK_WEBHOOK_URL=<configured per environment>
TZ=America/New_York
```

## County Status (Last Updated: 2026-04-14)

### ✅ Passing
Charlotte, DeSoto, Hendry, Hillsborough, Manatee, Sarasota, Orange, Palm Beach, Seminole, Pinellas, Polk, Brevard, Martin, Lake

### 🔧 Recently Fixed
- **Collier**: Function name mismatch + print instead of return
- **Osceola**: Argument mismatch in subprocess call
- **Highlands**: DrissionPage import guard added
- **Indian River**: Rewritten to extract from listing page (SPA detail pages)
