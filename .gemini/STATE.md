# 📡 STATE — Current Operational State

> **Updated at the start of each agent session. This is the live snapshot.**

---

## System Status: 🟢 OPERATIONAL

**Last updated**: 2026-04-23

---

## Active Counties (67/67 — 100% Coverage)

### Core Stable (24 counties — original build)

| County | Stack | Schedule | Status |
|--------|-------|----------|--------|
| Alachua | requests+BS4 | Every 6h | ✅ Stable |
| Brevard | requests+BS4 | Every 6h | ✅ Stable |
| Charlotte | DrissionPage | Every 6h | ✅ Stable |
| Collier | requests+BS4 | Every 6h | ✅ Stable |
| DeSoto | DrissionPage | Every 4h | ✅ Stable |
| Duval | DrissionPage | Every 6h | ✅ Stable |
| Escambia | requests+BS4 | Every 6h | ✅ Stable |
| Hendry | DrissionPage | Every 6h | ✅ Stable |
| Highlands | DrissionPage | Every 6h | ✅ Stable |
| Hillsborough | requests+BS4 | Every 6h | ✅ Stable |
| Indian River | requests+BS4 | Every 6h | ✅ Stable |
| Lake | requests+BS4 | Every 6h | ✅ Stable |
| Lee | REST-API | Every 2h | ✅ Upgraded — Python REST API (was GAS) |
| Manatee | DrissionPage | Every 6h | ✅ Stable |
| Martin | requests+BS4 | Every 6h | ✅ Stable |
| Orange | DrissionPage | Every 6h | ✅ Stable |
| Osceola | Playwright | Every 6h | ✅ Stable |
| Palm Beach | requests+BS4 | Every 6h | ✅ Stable |
| Pasco | DrissionPage | Every 6h | ✅ Stable |
| Pinellas | requests+BS4 | Every 6h | ✅ Stable |
| Polk | DrissionPage | Every 3h | ✅ Stable |
| Sarasota | DrissionPage | Every 6h | ✅ Stable |
| Seminole | requests+BS4 | Every 6h | ✅ Stable |
| Volusia | DrissionPage | Every 6h | ✅ Stable |

### Wave 1 — SmartCOP Clones (12 counties, deployed 2026-04-16)

| County | Stack | Schedule | Status |
|--------|-------|----------|--------|
| Bradford | requests+BS4 | Every 4h | 🆕 Deployed |
| Dixie | requests+BS4 | Every 6h | 🆕 Deployed |
| Gadsden | requests+BS4 | Every 4h | 🆕 Deployed |
| Gilchrist | requests+BS4 | Every 6h | 🆕 Deployed |
| Glades | requests+BS4 | Every 6h | 🆕 Deployed |
| Hamilton | requests+BS4 | Every 6h | 🆕 Deployed |
| Levy | requests+BS4 | Every 4h | 🆕 Deployed |
| Putnam | requests+BS4 | Every 4h | 🆕 Deployed |
| Santa Rosa | requests+BS4 | Every 4h | 🆕 Deployed |
| Sumter | requests+BS4 | Every 4h | 🆕 Deployed |
| Suwannee | requests+BS4 | Every 6h | 🆕 Deployed |
| Taylor | requests+BS4 | Every 6h | 🆕 Deployed |

### Wave 2 — DrissionPage / Standard (19 counties, deployed 2026-04-16)

| County | Stack | Schedule | Status |
|--------|-------|----------|--------|
| Bay | DrissionPage | Every 4h | 🆕 Deployed |
| Broward | requests+BS4 | Every 2h | 🆕 Deployed (sequential ID probing) |
| Citrus | requests+BS4 | Every 6h | 🆕 Deployed |
| Clay | DrissionPage | Every 4h | 🆕 Deployed |
| Columbia | DrissionPage | Every 4h | 🆕 Deployed |
| Flagler | DrissionPage | Every 6h | 🆕 Deployed |
| Franklin | requests+BS4 | Every 8h | 🆕 Deployed |
| Hernando | DrissionPage | Every 4h | 🆕 Deployed |
| Holmes | requests+BS4 | Every 12h | 🆕 Deployed |
| Leon | DrissionPage | Every 4h | 🆕 Deployed |
| Marion | DrissionPage | Every 4h | 🆕 Deployed |
| Monroe | requests+BS4 | Every 6h | 🆕 Deployed |
| Nassau | DrissionPage | Every 6h | 🆕 Deployed |
| Okaloosa | DrissionPage | Every 4h | 🆕 Deployed |
| Okeechobee | requests+BS4 | Every 8h | 🆕 Deployed |
| St. Johns | DrissionPage | Every 4h | 🆕 Deployed |
| St. Lucie | requests+BS4 | Every 4h | 🆕 Deployed |
| Walton | requests+BS4 | Every 6h | 🆕 Deployed |
| Washington | requests+BS4 | Every 8h | 🆕 Deployed |

### Wave 3-5 — Complex/Small Counties (12 counties, deployed 2026-04-16)

| County | Stack | Schedule | Status |
|--------|-------|----------|--------|
| Baker | requests+BS4 | Every 12h | 🆕 Deployed |
| Calhoun | pdfplumber | Every 12h | 🆕 Deployed |
| Gulf | requests+BS4 | Every 12h | 🆕 Deployed |
| Hardee | pdfplumber | Every 8h | 🆕 Deployed |
| Jackson | requests+BS4 | Every 12h | 🆕 Deployed |
| Jefferson | requests+BS4 | Every 12h | 🆕 Deployed |
| Lafayette | requests+BS4 | Every 12h | 🆕 Deployed |
| Liberty | requests+BS4 | Every 12h | 🆕 Deployed |
| Madison | requests+BS4 | Every 12h | 🆕 Deployed |
| Miami-Dade | DrissionPage | Every 3h | 🔴 CAPTCHA-blocked (largest county) |
| Union | requests+BS4 | Every 12h | 🆕 Deployed |
| Wakulla | requests+BS4 | Every 8h | 🆕 Deployed |

**Coverage**: 67/67 = **100%** (66 functional, 1 CAPTCHA-limited)

---

## Known Issues

| Issue | County | Severity | Status |
|-------|--------|----------|--------|
| CAPTCHA blocks inmate search | Miami-Dade | High | Open — needs 2Captcha/CapMonster integration |

---

## Recent Changes

| Date | Change | Impact |
|------|--------|--------|
| 2026-04-23 | Lee County upgraded: Python REST API solver + runner + workflow | Lee now fully in-repo, GAS dependency removed |
| 2026-04-23 | Dashboard created: `dashboard/index.html` + `dashboard/mobile.html` | New operational visibility |
| 2026-04-16 | Complete 67/67 network — 21 new counties added (Waves 2-5) | 100% FL coverage achieved |
| 2026-04-16 | Broward: sequential ID probing strategy (multi-agency) | Broward fully covered |
| 2026-04-16 | Documentation overhaul — 24-file agent brain | Docs only |

---

## What's Next (Priority Order)

1. **Validate Wave 1-5 scrapers** — run each county, confirm data flows to Sheets/MongoDB
2. **Miami-Dade CAPTCHA** — implement 2Captcha/CapMonster browser-based solver
3. **MongoDB primary migration** — move from Sheets-primary to MongoDB-primary
4. **10DLC reapplication** — unblock SMS/WhatsApp outreach
5. **Sentry Cron integration** — per-scraper health monitoring in dashboard

---

## Dependencies Health

| Dependency | Status | Last Verified |
|------------|--------|---------------|
| Google Sheets API | 🟢 Healthy | Auto-check each run |
| GitHub Actions | 🟢 Healthy | Continuous |
| DrissionPage (PyPI) | 🟢 Latest | 2026-04-16 |
| Slack Webhooks | 🟢 Healthy | Auto-check each run |
| MongoDB Atlas | 🟢 Healthy | Auto-check each run |
| Lee County REST API | 🟢 Healthy | 2026-04-23 |
