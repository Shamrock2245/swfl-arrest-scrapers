---
name: county-scraper-builder
description: >
  Use this skill when creating a new county arrest scraper, modifying an existing solver,
  or adding a new county to the scraping pipeline. Contains the canonical architecture,
  naming conventions, and integration checklist.
---

# County Scraper Builder

This skill contains everything needed to build, integrate, and deploy a new county arrest scraper.

## Architecture

```
counties/{county_name}/
├── solver.py        # The scraper logic — MUST export scrape_{county_name}()
├── runner.py        # Universal pipeline runner (identical across all counties)
├── __init__.py      # Empty, makes it a Python package
└── config.yaml      # → config/counties/{county_name}.yaml

.github/workflows/
└── scrape_{county_name}.yml   # GitHub Actions cron workflow

config/counties/
└── {county_name}.yaml         # County-specific config overrides
```

## Critical Conventions

### 1. Solver Function Naming — `scrape_{county_name}()`
The universal runner (`counties/{name}/runner.py`) dynamically imports the solver and looks for functions in this order:
1. `scrape_{county_name}()` ← **MUST USE THIS**
2. `scrape()`
3. `main()`

**The function name MUST match the directory name exactly.**

```python
# ✅ CORRECT — counties/collier/solver.py
def scrape_collier(days_back=7, max_pages=10):
    ...
    return records  # MUST return a list of dicts

# ❌ WRONG — will cause "No scrape function found" error
def scrape_county():
    ...
    print(json.dumps(records))  # DON'T print — RETURN the list
```

### 2. Solver Return Type
- MUST return a `list[dict]` of record dicts
- NEVER print JSON to stdout — the runner expects a return value
- Return `[]` on error, not `None` (None triggers `sys.exit(1)` in the runner)
- Each dict should have keys matching the 39-column `HEADER_ROW` in `core/writers/sheets_writer.py`

### 3. Solver Parameters
Accept `days_back` and `max_pages` as keyword arguments with defaults:
```python
def scrape_{county}(days_back=7, max_pages=10):
```
The runner passes these via `inspect.signature()` introspection — only args that exist in the signature get passed.

### 4. Logging
- Use `sys.stderr.write()` for progress/debug logs (not `print()`)
- `print()` to stdout is reserved for JSON output when running standalone via `__main__`

### 5. Record Dict Keys
Required keys for proper pipeline processing:
```python
{
    "County": "County Name",        # Required — used in dedup key
    "Booking_Number": "2025-12345", # Required — used in dedup key
    "Full_Name": "Last, First",     # Required — primary identifier
    "State": "FL",                  # Always "FL"
}
```

### 6. Website Stack Detection
Before writing a solver, determine the site's tech stack:
| Stack | Tool | Example Counties |
|-------|------|-----------------|
| Static HTML | `requests` + `BeautifulSoup` | Indian River, Collier |
| ASP.NET forms | `curl_cffi` + `BeautifulSoup` | Collier (fallback) |
| React SPA / Cloudflare | `DrissionPage` (ChromiumPage) | Highlands, Charlotte |
| Playwright-dependent | `playwright.sync_api` | Osceola |
| API-first | `requests` (JSON endpoints) | Palm Beach, Pinellas |

## New County Checklist

- [ ] Create `counties/{name}/solver.py` with `scrape_{name}()` function
- [ ] Create `counties/{name}/__init__.py` (empty file)
- [ ] Copy universal `runner.py` from any existing county
- [ ] Create `config/counties/{name}.yaml` (copy `_defaults.yaml` and customize)
- [ ] Create `.github/workflows/scrape_{name}.yml` workflow
- [ ] Test locally: `python counties/{name}/solver.py --days-back 3`
- [ ] Test via runner: `python counties/{name}/runner.py --days-back 3 --dry-run`
- [ ] Push and verify GitHub Actions green

## Workflow Template
```yaml
name: Scrape {County} County
on:
  schedule:
    - cron: 'MM HH,HH,HH,HH * * *'  # Stagger by 5-10 min from other counties
  workflow_dispatch:
jobs:
  scrape:
    uses: ./.github/workflows/scrape.yml
    with:
      county: {county_name}
      script: counties/{county_name}/runner.py
      args: "--days-back 7"
      needs_xvfb: true  # Set to true if solver uses a browser
    secrets: inherit
```

## Known Gotchas

- `[2026-04-14]` **Collier**: Used `scrape_county()` instead of `scrape_collier()` — runner couldn't find it
- `[2026-04-14]` **Collier**: Printed JSON to stdout instead of returning a list — runner got `None`
- `[2026-04-14]` **Indian River**: Detail pages (`/booking-details/{id}`) are JS-rendered SPAs — `requests` gets empty shells. Extract from listing page instead.
- `[2026-04-14]` **Osceola**: Uses old-style runner (`python_scrapers/scrapers/run_osceola.py`) that calls solver via subprocess with `--start` date format, not `--days-back`
- `[2026-04-14]` **Highlands**: DrissionPage requires Chromium binary — wrap import in try/except
