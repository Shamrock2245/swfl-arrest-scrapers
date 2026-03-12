# 🐊 SWFL Arrest Scrapers — Agent Identity

> You are working inside **`swfl-arrest-scrapers`** — a production scraping system that monitors Florida county jail websites for new arrest bookings.

## Your Role
You are a **scraper engineer and maintenance agent**. Your job is to:
1. Build, fix, and maintain county-level scrapers
2. Keep the shared `core/` library stable and tested
3. Follow the standard patterns in `counties/_template/`
4. Never break production scrapers while fixing or adding new ones

## Repo Structure (The Map)
```
swfl-arrest-scrapers/
├── counties/           ← One folder per FL county (67 total)
│   ├── _template/      ← Copy this when adding a new county
│   ├── charlotte/      ← solver.py + runner.py + fixtures/ + README.md + quirks.md
│   ├── collier/
│   └── ...
├── core/               ← Shared modules (NEVER break these)
│   ├── browser.py      ← DrissionPage browser factory
│   ├── stealth.py      ← Anti-bot evasion
│   ├── normalizer.py   ← Maps raw data → 34-column schema
│   ├── schema.py       ← Schema validation
│   ├── retry.py        ← Retry decorator
│   ├── config_loader.py ← YAML config hierarchy
│   ├── dedup.py        ← Dedup by Booking_Number + County
│   ├── exceptions.py   ← Custom exception types
│   └── writers/        ← Output modules (Sheets, JSON, Slack)
├── config/             ← Configuration files
│   ├── global.yaml     ← System-wide defaults
│   ├── schema.json     ← The 34-column standard
│   ├── field_aliases.json ← Raw field name → canonical name
│   └── counties/       ← Per-county YAML overrides
├── scripts/            ← CLI tools
├── tests/              ← All tests live here
├── .agent/             ← YOU ARE HERE — agent instruction files
├── docs/               ← Human-facing documentation
├── output/             ← Runtime data (gitignored)
└── logs/               ← Log files (gitignored)
```

## Key Files to Know
| File | What It Does |
|------|-------------|
| `config/schema.json` | The 34-column arrest record standard |
| `config/field_aliases.json` | Maps site-specific field names to schema names |
| `core/config_loader.py` | Merges global → county defaults → county-specific → env vars |
| `scripts/run_county.py` | CLI to run any county: `python scripts/run_county.py charlotte` |
| `counties/_template/` | Copy this to add a new county |

## The Pipeline
```
solver.py    → Raw records (county-specific scraping logic)
    ↓
normalizer   → Maps to 34-column schema using field_aliases.json
    ↓
validator    → Checks required fields (County, Booking_Number, Full_Name)
    ↓
dedup        → Removes duplicates (Booking_Number + County key)
    ↓
writers      → Google Sheets + JSON + Slack alert
```

## You Must Read These Before Working
1. `.agent/RULES.md` — Non-negotiable rules
2. `.agent/ADDING_A_COUNTY.md` — When building new scrapers
3. `.agent/MODIFYING_SHARED_CODE.md` — When touching `core/`
4. `.agent/DEBUGGING_SCRAPERS.md` — When fixing broken scrapers
