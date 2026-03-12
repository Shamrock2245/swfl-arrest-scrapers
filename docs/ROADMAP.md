# 🗺️ ROADMAP.md — Strategic Expansion Plan

> **From 14 counties to 67. From a scraper project to the statewide arrest intelligence network.**

---

## Current State (March 2026)

| Metric | Value |
|---|---|
| Active counties | 14 |
| Total Florida counties | 67 |
| Coverage | 21% |
| Primary engine | Python/DrissionPage |
| Secondary engine | Node.js/Puppeteer (legacy) |
| Storage | Google Sheets + MongoDB Atlas |
| Alerts | Slack (12+ channels) |
| CI/CD | GitHub Actions (10 workflows) |
| Infrastructure | Docker + GH Actions |

---

## Expansion Waves

### ✅ Wave 0 — Foundation (Complete)
**Timeline:** Q3 2025 – Q1 2026
- ☑ Lee (GAS internal)
- ☑ Charlotte (Python)
- ☑ Collier (GAS)
- ☑ DeSoto (Node.js)
- ☑ Hendry (Python)
- ☑ Hillsborough (Python)
- ☑ Manatee (Python)
- ☑ Sarasota (Python)
- ☑ Orange (Python)
- ☑ Osceola (Python)
- ☑ Palm Beach (Python)
- ☑ Pinellas (Python)
- ☑ Polk (Python)
- ☑ Seminole (Python)

### 🔄 Wave 1 — SmartCOP Blitz (13 counties, ~6.5 hours)
**Timeline:** Q2 2026
**Strategy:** Clone DeSoto script → change URL → test → deploy

Target counties: Bradford, Dixie, Escambia, Gadsden, Gilchrist, Glades, Hamilton, Levy, Putnam, Santa Rosa, Sumter, Suwannee, Taylor

**Effort:** ~30 min per county
**Post-wave target:** 27 counties (40% coverage)

### 🔜 Wave 2 — DrissionPage Standard (19 counties, ~30-60 hours)
**Timeline:** Q3 2026
**Strategy:** Standard DP scraper build per county

Target counties: Alachua, Bay, Brevard, Citrus, Clay, Columbia, Franklin, Hernando, Highlands, Holmes, Indian River, Lake, Leon, Marion, Martin, Monroe, Okeechobee, St. Johns, St. Lucie

**Effort:** 1–3 hours per county
**Post-wave target:** 46 counties (69% coverage)

### 🔮 Wave 3 — Complex Targets (13 counties, ~50-100 hours)
**Timeline:** Q4 2026
**Strategy:** Custom solutions per county — CAPTCHAs, SPAs, heavy JS

Target counties: Broward, Duval, Flagler, Miami-Dade, Nassau, Okaloosa, Pasco, Volusia, Walton, Washington, Baker, Hendry (re-eval), Sumter (re-eval)

**Effort:** 3–8 hours per county
**Post-wave target:** 59 counties (88% coverage)

### 📋 Wave 4 — PDF & Non-Standard (3 counties, ~10 hours)
**Timeline:** Q1 2027
**Strategy:** PDF parsing with `pdfplumber`, email monitoring

Target counties: Calhoun, Hardee, Polk (PDF mode)

**Post-wave target:** 62 counties (93% coverage)

### 🔍 Wave 5 — Manual Investigation (5 counties)
**Timeline:** Q1-Q2 2027
**Strategy:** Investigate feasibility, some may be app-only

Target counties: Gulf, Jackson, Jefferson, Lafayette, Liberty, Madison, Wakulla

**Post-wave target:** 67 counties (100% coverage) 🎯

---

## Infrastructure Evolution

| Phase | Current | Target | Timeline |
|---|---|---|---|
| **Execution** | GH Actions (shared runners) | GH Actions + Self-hosted runners | Q3 2026 |
| **Storage** | Google Sheets (primary) + MongoDB (secondary) | MongoDB (primary) + Sheets (backup) | Q4 2026 |
| **Scheduling** | Per-county GH Actions cron | Centralized scheduler (Node-RED or dedicated) | Q2 2027 |
| **Monitoring** | Ingestion_Log + Slack alerts | Dedicated health dashboard | Q3 2026 |
| **Proxy** | None (direct IPs) | Rotating proxy pool for high-block counties | When needed |
| **Containerization** | Docker Compose (local) | Docker Swarm or K8s for production | Q1 2027 |

---

## Feature Pipeline

| Feature | Priority | Effort | Target |
|---|---|---|---|
| **Real-time Slack dashboards** | 🔴 High | Medium | Q2 2026 |
| **ML-based lead scoring** | 🟡 Medium | High | Q4 2026 |
| **Court date prediction** | 🟡 Medium | High | Q1 2027 |
| **Automated fixture regression testing** | 🔴 High | Medium | Q2 2026 |
| **Per-county health dashboard** | 🔴 High | Medium | Q3 2026 |
| **WhatsApp alert integration** | 🟡 Medium | Low | Q2 2026 |
| **Telegram feed for hot leads** | 🟡 Medium | Low | Q2 2026 |
| **Self-hosted runner fleet** | 🟡 Medium | Medium | Q3 2026 |
| **Historical analytics dashboard** | 🟢 Low | High | 2027 |

---

## Integration Roadmap

| Integration | Source | Destination | Status |
|---|---|---|---|
| Sheets → Node-RED Dashboard | `Qualified_Arrests` tab | Bounty Board | ✅ Live |
| Sheets → Slack | `SheetsWriter` post-write hook | Per-county channels | ✅ Live |
| Sheets → GAS Lead Scoring | `Qualified_Arrests` tab | `LeadScoringSystem.gs` | ✅ Live |
| MongoDB → Analytics | Atlas cluster | Future dashboard | 🔄 Planned |
| Slack → WhatsApp | Hot lead alerts | Twilio WhatsApp relay | 📋 Queued |
| Slack → Telegram | Hot lead alerts | `@ShamrockBail_bot` | 📋 Queued |

---

## Key Milestones

| Milestone | Target Date | Status |
|---|---|---|
| 14 counties active | Mar 2026 | ✅ Complete |
| Documentation system v3.0 | Mar 2026 | ✅ Complete |
| Wave 1 (SmartCOP) complete | Jun 2026 | 📋 Planned |
| 30+ counties active | Jul 2026 | 📋 Planned |
| MongoDB primary storage | Oct 2026 | 📋 Planned |
| 50+ counties active | Dec 2026 | 📋 Planned |
| 67/67 counties (100%) | Q2 2027 | 🎯 Goal |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
