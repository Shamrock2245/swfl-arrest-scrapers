# SWFL Arrest Scrapers — Agent Context

## Mission
Build and maintain a **67-county Florida arrest scraping network** that feeds real-time booking data into the Shamrock Bail Bonds lead pipeline. Currently at **18 counties active** (2 more than originally listed because we expanded beyond SWFL). Every new county directly increases revenue and geographic reach.

Lee County is handled by the GAS internal scraper (in `shamrock-bail-portal-site/backend-gas/`), not this repo. It has a config here for reference only.

## Pipeline Architecture
```
County Jail Website → solver.py (scrape) → runner.py (pipeline)
    → Google Sheets (34-col arrest row)
    → MongoDB Atlas (via Cloud Functions proxy)
    → Slack (#new-arrests-{county})
```

## Repository Structure
```
counties/{name}/          # One folder per county
  solver.py               # Scraping logic — THE critical file
  runner.py               # Universal pipeline runner (identical everywhere)
  __init__.py             # Makes it a Python package

python_scrapers/scrapers/ # Old-style runners (subprocess-based, being phased out)
  run_{name}.py           # These call solver.py via subprocess

config/counties/          # YAML config per county
  {name}.yaml             # Scraping config, schedule, output tab name

core/                     # Shared library code
  config_loader.py        # Loads YAML configs
  writers/                # Output writers
    sheets_writer.py      # Google Sheets output (39-col HEADER_ROW)

.github/workflows/        # GitHub Actions cron jobs
  scrape_{name}.yml       # One workflow per county
  scrape.yml              # Reusable workflow template

creds/                    # Created at runtime by workflows
  service-account-key.json
```

## Critical Conventions
1. **Function name = directory name**: `counties/collier/solver.py` MUST export `scrape_collier()`
2. **Return a list**: Solver functions MUST `return records` (list of dicts), never `print()`
3. **Parameters**: Always accept `days_back=7, max_pages=10` kwargs
4. **Logging**: `sys.stderr.write()` for progress, `print()` only in `__main__` CLI
5. **Dedup key**: `Booking_Number` + `County` — both required in every record
6. **Error handling**: Return `[]` on failure, never `None` or raise unhandled exceptions

## County Status (18 Active)
| County | Stack | Status |
|--------|-------|--------|
| Brevard | requests+BS4 | ✅ |
| Charlotte | DrissionPage | ✅ |
| Collier | requests+BS4 | ✅ (fixed 2026-04-14) |
| DeSoto | DrissionPage | ✅ |
| Hendry | DrissionPage | ✅ |
| Highlands | DrissionPage | ✅ (fixed 2026-04-14) |
| Hillsborough | requests+BS4 | ✅ |
| Indian River | requests+BS4 | ✅ (fixed 2026-04-14) |
| Lake | requests+BS4 | ✅ |
| Lee | GAS Internal | ✅ (not in this repo) |
| Manatee | DrissionPage | ✅ |
| Martin | requests+BS4 | ✅ |
| Orange | DrissionPage | ✅ |
| Osceola | Playwright | ✅ (fixed 2026-04-14) |
| Palm Beach | requests+BS4 | ✅ |
| Pinellas | requests+BS4 | ✅ |
| Polk | DrissionPage | ✅ |
| Sarasota | DrissionPage | ✅ |
| Seminole | requests+BS4 | ✅ |

## Remaining 49 Counties (Expansion Targets)
Priority order based on population, bond volume, and geographic proximity:
1. **Tier 1** (High population, high bond volume): Duval (Jacksonville), Miami-Dade, Broward, Pasco, Volusia, St. Lucie
2. **Tier 2** (Medium population): Escambia, Leon, Alachua, Marion, Okaloosa, Bay, St. Johns, Flagler, Hernando, Citrus, Sumter, Putnam, Columbia
3. **Tier 3** (Smaller counties): Remaining 30 counties

## Environment Variables
```
GOOGLE_SHEETS_ID=121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=creds/service-account-key.json
SLACK_WEBHOOK_URL=<from secrets>
TZ=America/New_York
```

## Skills
See `.gemini/skills/` for specialized agent skills:

### Core Skills (Custom)
- `self-improving-agent/` — Post-task learning loop with multi-memory architecture
- `county-scraper-builder/` — New county setup guide, naming conventions, checklist
- `scraper-debugger/` — 7 common failure modes, diagnostic procedures
- `county-expansion/` — 67-county roadmap, site recon, lead analysis strategy

### Community Skills (Adapted from skills.sh)
- `systematic-debugging/` — 4-phase root cause analysis (from obra/superpowers)
- `github-actions-docs/` — Workflow writing, cron scheduling, CI/CD (from xixu-me/skills)
- `playwright-scraping/` — DrissionPage/Playwright anti-bot patterns (from currents-dev)
- `google-sheets-integration/` — 39-col schema, dedup, Sheets API patterns (from googleworkspace)
