# 🗺️ COUNTY_REGISTRY.md — Master County Reference

> **67 counties. One pipeline. Zero missed arrests.**

---

## Active Counties (Production)

| County | Stack | Schedule | Status | Known Quirks |
|---|---|---|---|---|
| **Charlotte** | Python/DrissionPage | Every 30m | ✅ Stable | ColdFusion site; date format varies |
| **Collier** | Apps Script (GAS) | Every 30m | ✅ Stable | Requires disclaimer acceptance |
| **DeSoto** | Node.js/Puppeteer | Every 60m | ✅ Legacy | SmartCOP system; incremental scrape |
| **Hendry** | Python/DrissionPage | Every 2h | ✅ Stable | Low volume county; API-based |
| **Hillsborough** | Python/DrissionPage | Every 20m | ✅ Stable | ASP.NET ViewState; high volume |
| **Lee** | Apps Script (GAS) | Every 30m | ✅ Stable | Internal GAS scraper via booking search |
| **Manatee** | Python/DrissionPage | Every 30m | ✅ Stable | Arrest inquiry form submission |
| **Orange** | Python/DrissionPage | Every 30m | ✅ Stable | PDF-based roster + web scraping |
| **Osceola** | Python/DrissionPage | Every 60m | ✅ Stable | Corrections report search form |
| **Palm Beach** | Python/DrissionPage | Every 30m | ⚠️ Beta | High volume; occasional timeouts |
| **Pinellas** | Python/DrissionPage | Every 30m | ✅ Stable | Disclaimer + search; high volume |
| **Polk** | Python/DrissionPage | Every 60m | ✅ Stable | HTML table; straightforward |
| **Sarasota** | Python/DrissionPage | Every 30m | ✅ Stable | Cloudflare strict mode; DP required |
| **Seminole** | Python/DrissionPage | Every 60m | ✅ Stable | WebBond/Inmates ASP.NET |

---

## Expansion Waves

### Wave 1 — SmartCOP Clones (Fastest to Implement)
These counties use the **SmartCOP/SmartWEB** jail management system — identical to DeSoto. Clone the DeSoto script and change the URL.

| County | URL | Difficulty | Priority |
|---|---|---|---|
| **Bradford** | `smartweb.bradfordsheriff.org` | 🟢 Easy | High |
| **Dixie** | `smartcop.dixiecountysheriff.com` | 🟢 Easy | Medium |
| **Escambia** | `inmatelookup.myescambia.com` | 🟢 Easy | High |
| **Gadsden** | `gadsdensheriff.com` | 🟢 Easy | Low |
| **Gilchrist** | `gcso.us` | 🟢 Easy | Low |
| **Glades** | `smartweb.gladessheriff.org` | 🟢 Easy | Low |
| **Hamilton** | `inmate.hamiltonsheriff.com` | 🟢 Easy | Low |
| **Levy** | `levyso.com` | 🟢 Easy | Low |
| **Putnam** | `smartweb.pcso.us` | 🟢 Easy | Medium |
| **Santa Rosa** | `santarosasheriff.org` | 🟢 Easy | Medium |
| **Sumter** | `portal.sumtercountysheriff.org` | 🟢 Easy | Low |
| **Suwannee** | `smartcop.suwanneesheriff.com` | 🟢 Easy | Low |
| **Taylor** | `smartcop.taylorsheriff.org` | 🟢 Easy | Low |

**Estimated effort per county:** 30 minutes (clone + URL swap + test)

---

### Wave 2 — DrissionPage Standard (Medium Effort)
Counties with standard web forms that DrissionPage handles easily.

| County | URL | Difficulty | Notes |
|---|---|---|---|
| **Alachua** | `acso.us/inmate-search/` | 🟡 Medium | POST search form |
| **Brevard** | `brevardsheriff.com/bookings/` | 🟢 Easy | Simple HTML bookings page |
| **Citrus** | `sheriffcitrus.org` | 🟢 Easy | Simple PHP recent arrests |
| **Clay** | `claysheriff.policetocitizen.com` | 🟡 Medium | P2C system; disclaimer click |
| **Columbia** | `50.204.15.10` | 🟡 Medium | SmartCOP via IP |
| **Franklin** | `franklinsheriff.com` | 🟡 Medium | Check for 'I Accept' splash |
| **Hernando** | `hernandosheriff.org` | 🟡 Medium | ASP.NET search form |
| **Highlands** | `highlandssheriff.org` | 🟡 Medium | Interactive search |
| **Holmes** | `holmescosheriff.org` | 🟡 Medium | Check if simple HTML |
| **Indian River** | `ircsheriff.org` | 🟡 Medium | Interactive search form |
| **Lake** | `lcso.org/inmates/` | 🟡 Medium | Interactive search |
| **Leon** | `leoncountyso.com` | 🟡 Medium | Search portal |
| **Marion** | `jail.marionso.com` | 🟡 Medium | Search form |
| **Martin** | `mcsofl.org` | 🟢 Easy | Recent Bookings page |
| **Monroe** | `keysso.net/arrests` | 🟡 Medium | Current inmates list |
| **Okeechobee** | `okeesheriff.org` | 🟡 Medium | Inmate search form |
| **St. Johns** | `sjso.org` | 🟡 Medium | Inmate search |
| **St. Lucie** | `stluciesheriff.com` | 🟡 Medium | Inmate lookup |
| **Washington** | `wcso.us/inmateRoster` | 🟡 Medium | Inmate roster |

**Estimated effort per county:** 1–3 hours

---

### Wave 3 — Complex Targets (High Effort)
Counties with heavy JS, CAPTCHAs, or unusual tech stacks.

| County | URL | Difficulty | Notes |
|---|---|---|---|
| **Bay** | `baysomobile.org` | 🟡 Medium | Mobile-optimized JS list |
| **Broward** | `sheriff.org` | 🔴 Hard | Captcha + ASP.NET search |
| **Duval** | `inmatesearch.jaxsheriff.org` | 🔴 Hard | Login required |
| **Flagler** | `nwwebcad.fcpsn.org` | 🔴 Hard | Tyler Tech/New World; very slow |
| **Miami-Dade** | `miamidade.gov` | 🔴 Hard | Complex search + Captcha |
| **Nassau** | `dssinmate.nassauso.com` | 🟡 Medium | Tyler Tech/New World |
| **Okaloosa** | `sheriff-okaloosa.org` | 🟡 Medium | Search form |
| **Osceola** | `osceola.org` | 🟡 Medium | Corrections report search |
| **Pasco** | `jailinfo.pascocorrections.net` | 🔴 Hard | Heavy JS SPA (#/inCustody) |
| **Pinellas** | `pcsoweb.com` | 🟡 Medium | Disclaimer + search |
| **Seminole** | `seminolesheriff.org` | 🟡 Medium | ASP.NET WebBond |
| **Volusia** | `volusiamug.vcgov.org` | 🟡 Medium | Mugshot-focused site |
| **Walton** | `nwscorrections.waltonso.org` | 🟡 Medium | Tyler Tech/New World |

**Estimated effort per county:** 3–8 hours

---

### Wave 4 — PDF/Non-Standard Sources
Counties that publish arrest data as PDFs or through non-web channels.

| County | URL | Difficulty | Notes |
|---|---|---|---|
| **Calhoun** | `mws-hrs.com/.../JailRosterReport.pdf` | 🟡 Medium | PDF → pdfplumber |
| **Hardee** | `hardeeso.com` | 🟡 Medium | PDF roster |
| **Polk** | `polksheriff.org` | 🟡 Medium | Often links to PDF |

**Estimated effort per county:** 2–4 hours

---

### Wave 5 — Manual Check / App Only
Counties that may not have accessible online rosters.

| County | URL | Difficulty | Notes |
|---|---|---|---|
| **Gulf** | `gulfsheriff.com` | 🔴 Unknown | Points to mobile app only |
| **Jackson** | `jacksoncountyfl.gov` | 🟡 Medium | Check search form |
| **Jefferson** | `jcso-fl.org` | 🔴 Unknown | May require login |
| **Lafayette** | `lafayetteso.org` | 🔴 Unknown | May not have online roster |
| **Liberty** | `libertycountysheriff.org` | 🔴 Unknown | Verify data exists |
| **Madison** | `madisonjail.org` | 🟡 Medium | Check specific jail site |
| **Wakulla** | `wcso.org` | 🔴 Unknown | Generic site |

---

## County Tech Stack Classification

| Tech Stack | Description | Strategy | Example Counties |
|---|---|---|---|
| **SmartCOP/SmartWEB** | Standardized jail mgmt platform | Clone DeSoto script | Bradford, Dixie, Escambia, Glades, etc. |
| **Tyler Tech/New World** | Enterprise corrections system | DrissionPage + long waits | Flagler, Nassau, Walton |
| **ASP.NET WebForms** | ViewState-heavy .NET apps | DrissionPage required | Hillsborough, Hernando, Seminole |
| **P2C (Police-to-Citizen)** | Public-facing platform | DrissionPage + disclaimer | Clay |
| **ColdFusion** | Adobe CF-based apps | DrissionPage or Requests | Charlotte |
| **PHP/Simple HTML** | Basic web pages | Requests/BS4 preferred | Citrus, Brevard |
| **PDF Rosters** | Downloaded PDF files | requests + pdfplumber | Calhoun, Hardee |
| **Mobile App Only** | No web access | Manual investigation | Gulf |
| **Custom/Unknown** | Non-standard implementations | DrissionPage (safe default) | Various |

---

## County Status Codes

| Code | Meaning |
|---|---|
| ✅ `STABLE` | Running in production, >95% success rate |
| ⚠️ `BETA` | Running but may have occasional issues |
| 🔄 `IN_PROGRESS` | Scraper being developed |
| ⏸️ `PAUSED` | Temporarily disabled (site down, blocked, etc.) |
| 📋 `QUEUED` | Identified but development not started |
| ❌ `BLOCKED` | Cannot be scraped (app-only, login-only, etc.) |
| 🔍 `RECON` | Needs investigation to determine viability |

---

## Key Metrics (Per County)

When a county reaches `STABLE` status, these metrics should be tracked:

| Metric | Target | Measured By |
|---|---|---|
| **Success Rate** | >95% of scheduled runs | `Ingestion_Log` |
| **Freshness** | Data ≤2 hours old | Timestamp comparison |
| **Avg Records/Run** | Varies by county | `Records_Found` avg |
| **Dedup Accuracy** | 100% (zero duplicate inserts) | `Ingestion_Log` |
| **Avg Duration** | <5 minutes per run | `Duration_Seconds` |

---
*Maintained by: Shamrock Engineering Team & AI Agents*
*Last Updated: March 2026*
