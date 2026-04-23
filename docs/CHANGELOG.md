# 📝 CHANGELOG — Scraper Network History

> **What changed, when, and why. Newest entries first.**

---

## 2026-04-23 — Lee County Python Upgrade + Dashboard Launch

### Added
- `counties/lee/solver.py` — Python REST API solver using `https://www.sheriffleefl.org/public-api/bookings/`
  - Replaces legacy GAS trigger entirely; Lee County now fully in-repo
  - Paginates through all bookings, normalizes to standard schema
  - Handles date filtering, charge extraction, mugshot URL
- `counties/lee/runner.py` — standard runner.py pattern
- `.github/workflows/scrape_lee.yml` — GitHub Actions workflow, runs every 2h
- `dashboard/index.html` — full-featured desktop dashboard
  - Shows all 67 counties with status badges (Stable / New / API / Blocked)
  - Grid and list view toggle, search, filter by status
  - Coverage progress bar (100%), links to source URLs
- `dashboard/mobile.html` — mobile-optimized dashboard
  - Sticky header with live badge counts
  - Touch-optimized filter pills, compact list view
  - iOS safe-area support

### Changed
- `.gemini/STATE.md` — updated from 24/67 to 67/67 (100% coverage)
- `.gemini/TASKS.md` — cleared completed Wave 1-5 tasks, added new priorities
- Lee County status: GAS Internal → Python REST-API (fully in-repo)

---

## 2026-04-16 — Complete 67/67 Florida County Network

### Added
- 21 new county scrapers (Waves 2-5 completion):
  - Wave 2 remaining: Clay, Franklin, Hernando, Holmes
  - Wave 3 remaining: Bay, Flagler, Nassau, Okaloosa, Walton
  - Wave 4 remaining: Calhoun, Hardee
  - Wave 5 all: Gulf, Jackson, Jefferson, Lafayette, Liberty, Madison, Wakulla
  - Final 3: Baker, Miami-Dade (CAPTCHA-limited), Union
- Broward County: sequential ID probing strategy
  - Multi-agency prefixes: BSO (50), Pompano Beach PD (23), Fort Lauderdale PD (57), Sunrise PD (25), US Marshals (90)
  - Binary search frontier detection per agency
- 21 new GitHub Actions workflows (`scrape_*.yml`)

### Changed
- `docs/SOURCES.md` — all waves marked complete
- Miami-Dade flagged as CAPTCHA-blocked

**Coverage milestone: 67/67 counties (100%) — 66 functional, 1 CAPTCHA-limited**

---

## 2026-04-16 — Documentation Overhaul

### Added
- 24-file documentation system (the "Agent Brain")
- `.gemini/`: IDENTITY, SYSTEM, AGENTS, BOUNDARIES, TOOLS, STATE, HEARTBEAT, MEMORY, TASKS, USER, REFLECTION, LOGBOOK
- `docs/`: DATA_SCHEMA, NORMALIZATION, SCORING, QUEUE, COMPLIANCE, OUTREACH_RULES, SECRETS, SCRAPING_RULES, ERRORS_AND_RECOVERY, SOURCES

### Removed
- `docs/SCHEMA.md` → replaced by `docs/DATA_SCHEMA.md`
- `docs/COUNTY_REGISTRY.md` → replaced by `docs/SOURCES.md`
- `docs/STEALTH_PLAYBOOK.md` → replaced by `docs/SCRAPING_RULES.md`
- `docs/OPERATIONS.md` → split into ERRORS_AND_RECOVERY + STATE + HEARTBEAT

### Changed
- `docs/CHANGELOG.md` — overhauled with real history (this file)
- `docs/ROADMAP.md` — updated counts and dates

---

## 2026-04-15 — Skills Consolidation

### Added
- `.gemini/skills/repo-conventions/SKILL.md` — consolidated from 5 old .agent/ files
- `.gemini/skills/testing-guide/SKILL.md` — consolidated from .agent/TESTING_GUIDE.md

### Removed
- Entire `.agent/` directory (12 files) — all unique content ported to `.gemini/skills/`

### Changed
- `.gemini/GEMINI.md` — updated to list all 15 skills
- `README.md` — removed all `.agent/` references, updated county count to 24
- `docs/README.md` — updated index to point to `.gemini/skills/`
- `docs/ARCHITECTURE.md` — updated repo layout diagram

---

## 2026-04-14 — Major County Expansion (14 → 24)

### Added
- 6 new counties: Alachua, Brevard, Duval, Escambia, Pasco, Volusia
- Each with `counties/{name}/solver.py`, `runner.py`, config YAML, GH Actions workflow

### Fixed
- Collier — migrated from GAS to requests+BS4 (faster, more reliable)
- Highlands — updated form submission for new search interface
- Indian River — updated selectors for redesigned results table
- Osceola — switched from DrissionPage to Playwright engine

### Changed
- Standardized `runner.py` template across all Python counties
- Introduced `json_writer` pattern for structured output
- Network-wide verification: 24/24 counties at 100% success rate

---

## 2026-03-05 — Documentation System v3.0

### Added
- `docs/SCHEMA.md` — 34-column universal data model
- `docs/COUNTY_REGISTRY.md` — 67-county master reference
- `docs/OPERATIONS.md` — runbook with SLOs and incident playbooks
- `docs/ROADMAP.md` — strategic expansion plan
- `docs/STEALTH_PLAYBOOK.md` — anti-detection reference
- `.agent/` documentation system (12 files)

### Changed
- Established SSoT (Single Source of Truth) documentation architecture

---

## 2026-Q1 — Wave 0 Complete (14 Counties)

### Counties Deployed
Charlotte, Collier, DeSoto, Hendry, Highlands, Hillsborough, Indian River, Lake, Lee (GAS), Manatee, Martin, Orange, Osceola, Palm Beach, Pinellas, Polk, Sarasota, Seminole

### Infrastructure
- Docker dual-stack (Python + Node.js)
- GitHub Actions CI/CD with staggered cron
- Google Sheets primary storage
- MongoDB Atlas secondary storage
- Slack alerting (12+ channels)
- 15 `.gemini/skills/` for agent capabilities

---

## Source Breakages (Historical)

| Date | County | Breakage | Resolution |
|------|--------|----------|------------|
| 2026-04-14 | Highlands | Search form submission changed | Updated form POST handling |
| 2026-04-14 | Indian River | Results table restructured | Updated CSS selectors |
| 2026-04-14 | Osceola | DrissionPage failing on page interactions | Switched to Playwright |
| 2026-03 | Sarasota | Cloudflare strict mode activated | DrissionPage headful + delays |
