# 🗺️ ROADMAP.md — Strategic Expansion Plan

> **From 24 counties to 67. From a scraper project to the statewide arrest intelligence network.**

---

## Current State (April 2026)

| Metric | Value |
|---|---|
| Active counties | **24** |
| Total Florida counties | 67 |
| Coverage | **36%** |
| Population covered | ~60% of Florida |
| Primary engine | Python (DrissionPage + requests/BS4) |
| Secondary engines | Playwright, Node.js/Puppeteer (legacy) |
| Storage | Google Sheets (primary) + MongoDB Atlas (secondary) |
| Alerts | Slack (12+ channels) |
| CI/CD | GitHub Actions (24 workflows) |
| Infrastructure | Docker + GH Actions |
| Success rate (7d) | ~100% |

---

## Expansion Waves

### ✅ Wave 0 — Foundation (Complete — 18 counties)
**Timeline:** Q3 2025 – Q1 2026
- ☑ Lee (GAS internal)
- ☑ Charlotte (DrissionPage)
- ☑ Collier (requests+BS4, migrated from GAS)
- ☑ DeSoto (DrissionPage)
- ☑ Hendry (DrissionPage)
- ☑ Highlands (DrissionPage)
- ☑ Hillsborough (requests+BS4)
- ☑ Indian River (requests+BS4)
- ☑ Lake (requests+BS4)
- ☑ Manatee (DrissionPage)
- ☑ Martin (requests+BS4)
- ☑ Orange (DrissionPage)
- ☑ Osceola (Playwright)
- ☑ Palm Beach (requests+BS4)
- ☑ Pinellas (requests+BS4)
- ☑ Polk (DrissionPage)
- ☑ Sarasota (DrissionPage)
- ☑ Seminole (requests+BS4)

### ✅ Wave 0.5 — Rapid Expansion (Complete — 6 counties)
**Timeline:** April 2026
- ☑ Alachua (requests+BS4)
- ☑ Brevard (requests+BS4)
- ☑ Duval (DrissionPage)
- ☑ Escambia (requests+BS4)
- ☑ Pasco (DrissionPage)
- ☑ Volusia (DrissionPage)

### 🔄 Wave 1 — SmartCOP Blitz (12 counties, ~6 hours)
**Timeline:** Q2 2026
**Strategy:** Clone DeSoto script → change URL → test → deploy

| County | URL | Est. Time |
|---|---|---|
| Bradford | `smartweb.bradfordsheriff.org` | 30m |
| Dixie | `smartcop.dixiecountysheriff.com` | 30m |
| Gadsden | `gadsdensheriff.com` | 30m |
| Gilchrist | `gcso.us` | 30m |
| Glades | `smartweb.gladessheriff.org` | 30m |
| Hamilton | `inmate.hamiltonsheriff.com` | 30m |
| Levy | `levyso.com` | 30m |
| Putnam | `smartweb.pcso.us` | 30m |
| Santa Rosa | `santarosasheriff.org` | 30m |
| Sumter | `portal.sumtercountysheriff.org` | 30m |
| Suwannee | `smartcop.suwanneesheriff.com` | 30m |
| Taylor | `smartcop.taylorsheriff.org` | 30m |

**Post-wave target:** 36 counties (54% coverage)

### 🔜 Wave 2 — Standard DrissionPage (10 counties, ~15-30 hours)
**Timeline:** Q3 2026
**Strategy:** Standard DP/requests build per county

| County | Difficulty | Notes |
|---|---|---|
| Citrus | 🟢 Easy | Simple PHP recent arrests |
| Clay | 🟡 Medium | P2C system; disclaimer click |
| Columbia | 🟡 Medium | SmartCOP via IP |
| Hernando | 🟡 Medium | ASP.NET search form |
| Leon | 🟡 Medium | Search portal |
| Marion | 🟡 Medium | Search form |
| Monroe | 🟡 Medium | Current inmates list |
| Okeechobee | 🟡 Medium | Inmate search form |
| St. Johns | 🟡 Medium | Inmate search |
| St. Lucie | 🟡 Medium | Inmate lookup — **high priority (Tier 1 pop)** |

**Post-wave target:** 46 counties (69% coverage)

### 🔮 Wave 3 — Complex Targets (9 counties, ~40-70 hours)
**Timeline:** Q4 2026
**Strategy:** Custom solutions per county — CAPTCHAs, SPAs, heavy JS

| County | Difficulty | Notes |
|---|---|---|
| **Miami-Dade** | 🔴 Hard | Complex search + Captcha — **#1 priority (population)** |
| **Broward** | 🔴 Hard | Captcha + ASP.NET — **#2 priority (population)** |
| Bay | 🟡 Medium | Mobile-optimized JS list |
| Flagler | 🔴 Hard | Tyler Tech/New World; very slow |
| Nassau | 🟡 Medium | Tyler Tech/New World |
| Okaloosa | 🟡 Medium | Search form |
| Walton | 🟡 Medium | Tyler Tech/New World |
| Franklin | 🟡 Medium | 'I Accept' splash |
| Holmes | 🟡 Medium | Check if simple HTML |
| Washington | 🟡 Medium | Inmate roster |

**Post-wave target:** 56 counties (84% coverage)

### 📋 Wave 4 — PDF & Non-Standard (3 counties, ~10 hours)
**Timeline:** Q1 2027
**Strategy:** PDF parsing with `pdfplumber`

Target counties: Calhoun, Hardee, Baker

**Post-wave target:** 59 counties (88% coverage)

### 🔍 Wave 5 — Manual Investigation (8 counties)
**Timeline:** Q1-Q2 2027
**Strategy:** Investigate feasibility, some may be app-only or have no online roster

Target counties: Gulf, Jackson, Jefferson, Lafayette, Liberty, Madison, Wakulla, Unknown remnants

**Post-wave target:** 67 counties (100% coverage) 🎯

---

## Infrastructure Evolution

| Phase | Current | Target | Timeline |
|---|---|---|---|
| **Execution** | GH Actions (shared runners) | GH Actions + Self-hosted runners | Q3 2026 |
| **Storage** | Google Sheets (primary) + MongoDB (secondary) | MongoDB (primary) + Sheets (backup) | Q4 2026 |
| **Scheduling** | Per-county GH Actions cron | Centralized scheduler (Node-RED or dedicated) | Q2 2027 |
| **Monitoring** | Ingestion_Log + Slack alerts | Sentry Crons + dedicated health dashboard | Q3 2026 |
| **Proxy** | None (direct IPs) | Rotating proxy pool for high-block counties | When needed |
| **Compliance** | Manual review | Automated compliance gate in pipeline | Q2 2026 |
| **Outreach** | SMS paused (10DLC) | WhatsApp + SMS via Twilio (10DLC approved) | Q2-Q3 2026 |

---

## Feature Pipeline

| Feature | Priority | Effort | Target |
|---|---|---|---|
| **Compliance gate (Stage 4)** | 🔴 High | Medium | Q2 2026 |
| **Automated fixture regression testing** | 🔴 High | Medium | Q2 2026 |
| **Per-county health dashboard** | 🔴 High | Medium | Q3 2026 |
| **Self-hosted runner fleet** | 🟡 Medium | Medium | Q3 2026 |
| **ML-based lead scoring** | 🟡 Medium | High | Q4 2026 |
| **Reason codes in production** | 🟡 Medium | Low | Q2 2026 |
| **WhatsApp alert integration** | 🟡 Medium | Low | Blocked (10DLC) |
| **Telegram feed for hot leads** | 🟡 Medium | Low | Q3 2026 |
| **Court date prediction** | 🟢 Low | High | Q1 2027 |
| **Historical analytics dashboard** | 🟢 Low | High | 2027 |

---

## Integration Roadmap

| Integration | Source | Destination | Status |
|---|---|---|---|
| Sheets → Node-RED Dashboard | `Qualified_Arrests` tab | Bounty Board | ✅ Live |
| Sheets → Slack | `SheetsWriter` post-write hook | Per-county channels | ✅ Live |
| Sheets → GAS Lead Scoring | `Qualified_Arrests` tab | `LeadScoringSystem.gs` | ✅ Live |
| Sheets → GAS Intake Hydration | Arrest record fields | `IntakeQueue` CMS | ✅ Live |
| MongoDB → Analytics | Atlas cluster | Future dashboard | 🔄 Planned |
| Slack → WhatsApp | Hot lead alerts | Twilio WhatsApp relay | ⏸️ Blocked (10DLC) |
| Slack → Telegram | Hot lead alerts | `@ShamrockBail_bot` | 📋 Queued |
| Pipeline → Sentry | Per-scraper health | Sentry Crons | 📋 Queued |

---

## Key Milestones

| Milestone | Target Date | Status |
|---|---|---|
| 14 counties active | Mar 2026 | ✅ Complete |
| Documentation system v3.0 | Mar 2026 | ✅ Complete |
| 24 counties active | Apr 2026 | ✅ Complete |
| 24-file agent brain | Apr 2026 | ✅ Complete |
| Wave 1 (SmartCOP) complete | Jun 2026 | 📋 Planned |
| 36+ counties active | Jul 2026 | 📋 Planned |
| MongoDB primary storage | Oct 2026 | 📋 Planned |
| 50+ counties active | Dec 2026 | 📋 Planned |
| 67/67 counties (100%) | Q2 2027 | 🎯 Goal |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: April 2026*
