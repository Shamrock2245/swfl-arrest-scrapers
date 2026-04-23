# 📋 TASKS — Active Task Queue

> **What needs to be done, in priority order. Updated each session.**

---

## 🔴 High Priority

- `[ ]` **Miami-Dade CAPTCHA Bypass**
  - Largest county in Florida — currently blocked by CAPTCHA on inmate search
  - Options: 2Captcha API, CapMonster, or Playwright + manual CAPTCHA solve
  - See `counties/miami_dade/solver.py` — solver exists, needs CAPTCHA integration

- `[ ]` **Validate Wave 1-5 Scrapers**
  - 43 new scrapers deployed 2026-04-16 — need live validation run
  - Run each solver, confirm records flow to Google Sheets + MongoDB
  - Flag any that return 0 records or throw errors

---

## 🟡 Medium Priority

- `[ ]` **MongoDB primary migration**
  - Move from Sheets-primary to MongoDB-primary storage
  - Sheets becomes secondary/backup
  - See `core/writers/` for current writer architecture

- `[ ]` **10DLC reapplication**
  - Unblock SMS/WhatsApp outreach (currently on hold)
  - Required for automated lead follow-up

- `[ ]` **Sentry Cron integration**
  - Add per-scraper health monitoring
  - Each GitHub Actions run should ping Sentry on success/failure
  - Dashboard should reflect real-time health status

- `[ ]` **Dashboard GitHub Pages deployment**
  - Deploy `dashboard/index.html` to GitHub Pages
  - Enable auto-update via GitHub Actions on each scraper run

---

## 🟢 Low Priority

- `[ ]` **ML-based lead scoring** — upgrade from rule-based to ML model
- `[ ]` **Court date prediction** — predict court dates from charge patterns
- `[ ]` **Historical analytics dashboard** — visualize arrest trends over time
- `[ ]` **Self-hosted runner fleet** — reduce dependency on GitHub shared runners

---

## ✅ Recently Completed

- `[x]` **Lee County Python scraper** — REST API solver + runner + workflow (2026-04-23)
  - Replaced legacy GAS trigger with native Python REST API solver
  - Endpoint: `https://www.sheriffleefl.org/public-api/bookings/`
  - Schedule: Every 2h via GitHub Actions

- `[x]` **Dashboard created** — `dashboard/index.html` + `dashboard/mobile.html` (2026-04-23)
  - Desktop: grid/list view, search, filter by status, 67-county coverage bar
  - Mobile: sticky header, touch-optimized filter pills, compact list view

- `[x]` **Complete 67/67 Florida county network** — 21 new counties (2026-04-16)
  - Wave 2 remaining: Clay, Franklin, Hernando, Holmes
  - Wave 3 remaining: Bay, Flagler, Nassau, Okaloosa, Walton
  - Wave 4 remaining: Calhoun, Hardee
  - Wave 5 all: Gulf, Jackson, Jefferson, Lafayette, Liberty, Madison, Wakulla
  - Final 3: Baker, Miami-Dade (CAPTCHA), Union

- `[x]` **Broward County** — sequential ID probing strategy (2026-04-16)
  - Multi-agency coverage: BSO, Pompano Beach PD, Fort Lauderdale PD, Sunrise PD, US Marshals
  - Binary search frontier detection per agency prefix

- `[x]` **SmartCOP Wave 1** — 12 counties cloned from DeSoto (2026-04-16)
  - Bradford, Dixie, Gadsden, Gilchrist, Glades, Hamilton, Levy, Putnam, Santa Rosa, Sumter, Suwannee, Taylor

- `[x]` **Documentation overhaul** — 24-file agent brain (2026-04-16)

- `[x]` **24-county core network** — stabilized to 100% success rate (2026-04-14)
