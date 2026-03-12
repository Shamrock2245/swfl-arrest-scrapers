# 📖 GLOSSARY.md — Domain Vocabulary & Abbreviations

> **Shared language = shared understanding. Use these terms consistently across all docs and code.**

---

## Core Concepts

| Term | Definition |
|---|---|
| **Arrest Record** | A single booking event from a county jail roster, containing defendant info, charges, bond amount, and custody status |
| **Booking Number** | The unique identifier assigned by the county jail at time of arrest. Combined with `County`, forms the composite primary key |
| **Bond** | The financial guarantee (paid to the court via a bail bondsman) that ensures a defendant returns for trial |
| **Bond Amount** | The dollar amount set by a judge that must be posted for the defendant's release |
| **Bondable** | An arrest where the defendant can legally post bail (not "No Bond" or capital offense) |
| **Composite Key** | The deduplication anchor: `County` + `Booking_Number`. Unique across all systems |
| **County Tab** | A sheet tab in the Master Google Sheet named after a county (e.g., `Charlotte`, `Hillsborough`) |
| **Dedup / Deduplication** | The process of ensuring no duplicate records exist using the composite key |
| **Fixture** | A saved HTML file from a county website, used for offline testing and regression comparison |
| **Hot Lead** | An arrest with `Lead_Score ≥ 70`. High commercial viability — triggers immediate outreach |
| **Idempotent** | An operation that produces the same result whether run once or 100 times |
| **Ingestion** | The process of scraping, normalizing, scoring, and storing an arrest record |
| **Lead Score** | A 0–100 numerical rating of an arrest's commercial viability for bail bonding |
| **Lead Status** | Classification: `Hot` (≥70), `Warm` (40–69), `Cold` (1–39), `Disqualified` (≤0) |
| **Mugshot** | Public photo taken at booking. URL stored in `Mugshot_URL` column |
| **Qualified Arrests** | Records with `Lead_Score ≥ 70`, mirrored to the `Qualified_Arrests` tab |
| **Roster** | A county jail's public list of current inmates (web page, PDF, or API) |
| **Runner** | The executable script that orchestrates a single county's scrape cycle (e.g., `run_charlotte.py`) |
| **Solver** | The core scraping logic for a county — navigates the site, extracts data (e.g., `charlotte_solver.py`) |
| **Upsert** | Insert if new, update if exists — the standard write operation |

---

## Technology Terms

| Term | Definition |
|---|---|
| **ASP.NET ViewState** | A hidden form field in .NET web apps that stores page state. Must be preserved between requests |
| **`cloudscraper`** | Python library that bypasses basic Cloudflare challenges. Insufficient for strict mode |
| **Cloudflare** | CDN and anti-bot service used by many county websites |
| **CAPTCHA** | "Completely Automated Public Turing test to tell Computers and Humans Apart" — puzzle/verification |
| **`clasp`** | Google's command-line tool for managing Apps Script projects |
| **`curl_cffi`** | Python library that mimics `curl` with TLS fingerprinting for stealth HTTP requests |
| **Docker** | Container platform that packages scrapers with all dependencies |
| **`docker-compose`** | Tool for defining and running multi-container Docker applications |
| **DrissionPage (DP)** | Python browser automation library using real Chromium — primary scraping engine |
| **ElevenLabs** | AI voice platform powering "Shannon" (after-hours voice agent) |
| **GAS (Google Apps Script)** | Server-side JavaScript platform; the "Brain" of Shamrock's backend |
| **GH Actions** | GitHub Actions — CI/CD platform running scheduled scraper workflows |
| **MongoDB Atlas** | Cloud-hosted MongoDB cluster used for centralized arrest data storage |
| **Node-RED** | Low-code automation platform running the Shamrock Operations Dashboard |
| **Puppeteer** | Node.js library for controlling Chromium. Used in legacy scrapers |
| **`pdfplumber`** | Python library for extracting text and tables from PDF files |
| **SignNow** | Electronic signature platform for bail bond documents |
| **SmartCOP / SmartWEB** | Jail management platform used by 13+ Florida counties. Standardized HTML structure |
| **Stealth Plugin** | `puppeteer-extra-plugin-stealth` — Puppeteer plugin to evade bot detection |
| **Turnstile** | Cloudflare's newer CAPTCHA alternative. Usually auto-solves in headful browsers |
| **Tyler Tech / New World** | Enterprise corrections software. Very slow page loads, complex JS |
| **Twilio** | Cloud communications platform for SMS and WhatsApp |
| **Velo** | Wix's JavaScript development platform for website functionality |
| **ViewState** | See ASP.NET ViewState |
| **Wix CMS** | Content Management System on the Shamrock bail portal website |

---

## Abbreviations

| Abbr | Full Form |
|---|---|
| **API** | Application Programming Interface |
| **BS4** | BeautifulSoup 4 (Python HTML parser) |
| **CCSO** | Charlotte County Sheriff's Office |
| **CDP** | Chrome DevTools Protocol |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **CMS** | Content Management System |
| **CSV** | Comma-Separated Values |
| **DP** | DrissionPage |
| **FCRA** | Fair Credit Reporting Act |
| **FL** | Florida |
| **GAS** | Google Apps Script |
| **GH** | GitHub |
| **HCSO** | Hillsborough County Sheriff's Office |
| **LCSO** | Lee County Sheriff's Office |
| **ML** | Machine Learning |
| **MDB** | MongoDB |
| **OOM** | Out of Memory |
| **P2C** | Police to Citizen (public records platform) |
| **PII** | Personally Identifiable Information |
| **PK** | Primary Key |
| **PR** | Pull Request |
| **ROR** | Release on Own Recognizance |
| **SA** | Service Account |
| **SLO** | Service Level Objective |
| **SPA** | Single Page Application |
| **SWFL** | Southwest Florida |
| **TLS** | Transport Layer Security |
| **UA** | User-Agent |

---

## County Codes

Standardized codes used in composite keys and logging:

| Code | County |
|---|---|
| `ALACHUA` | Alachua |
| `BAKER` | Baker |
| `BAY` | Bay |
| `BRADFORD` | Bradford |
| `BREVARD` | Brevard |
| `BROWARD` | Broward |
| `CALHOUN` | Calhoun |
| `CHARLOTTE` | Charlotte |
| `CITRUS` | Citrus |
| `CLAY` | Clay |
| `COLLIER` | Collier |
| `COLUMBIA` | Columbia |
| `DESOTO` | DeSoto |
| `DIXIE` | Dixie |
| `DUVAL` | Duval |
| `ESCAMBIA` | Escambia |
| `FLAGLER` | Flagler |
| `FRANKLIN` | Franklin |
| `GADSDEN` | Gadsden |
| `GILCHRIST` | Gilchrist |
| `GLADES` | Glades |
| `GULF` | Gulf |
| `HAMILTON` | Hamilton |
| `HARDEE` | Hardee |
| `HENDRY` | Hendry |
| `HERNANDO` | Hernando |
| `HIGHLANDS` | Highlands |
| `HILLSBOROUGH` | Hillsborough |
| `HOLMES` | Holmes |
| `INDIAN_RIVER` | Indian River |
| `JACKSON` | Jackson |
| `JEFFERSON` | Jefferson |
| `LAFAYETTE` | Lafayette |
| `LAKE` | Lake |
| `LEE` | Lee |
| `LEON` | Leon |
| `LEVY` | Levy |
| `LIBERTY` | Liberty |
| `MADISON` | Madison |
| `MANATEE` | Manatee |
| `MARION` | Marion |
| `MARTIN` | Martin |
| `MIAMI_DADE` | Miami-Dade |
| `MONROE` | Monroe |
| `NASSAU` | Nassau |
| `OKALOOSA` | Okaloosa |
| `OKEECHOBEE` | Okeechobee |
| `ORANGE` | Orange |
| `OSCEOLA` | Osceola |
| `PALM_BEACH` | Palm Beach |
| `PASCO` | Pasco |
| `PINELLAS` | Pinellas |
| `POLK` | Polk |
| `PUTNAM` | Putnam |
| `SANTA_ROSA` | Santa Rosa |
| `SARASOTA` | Sarasota |
| `SEMINOLE` | Seminole |
| `ST_JOHNS` | St. Johns |
| `ST_LUCIE` | St. Lucie |
| `SUMTER` | Sumter |
| `SUWANNEE` | Suwannee |
| `TAYLOR` | Taylor |
| `VOLUSIA` | Volusia |
| `WAKULLA` | Wakulla |
| `WALTON` | Walton |
| `WASHINGTON` | Washington |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
