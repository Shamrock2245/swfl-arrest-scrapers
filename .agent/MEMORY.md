# 🧠 Agent Memory

Persistent knowledge about the repo state. Updated by agents as they learn.

---

## Active Counties (Production)
| County | Stack | Status | Key Quirk |
|--------|-------|--------|-----------|
| Charlotte | Python | ✅ Active | Cloudflare, Revize CMS, 21-day lookback |
| Collier | Node.js | ✅ Active | ASP.NET postback pagination |
| DeSoto | Node.js | ✅ Active | Roster-style, incremental support |
| Hendry | Python | ✅ Active | Has REST API endpoint |
| Lee | Node.js | ✅ Active | Triggered via GAS internal scraper |
| Manatee | Python | ✅ Active | Cloudflare, Revize CMS (same as Charlotte) |

## In-Progress Counties
| County | Stack | Status | Blocker |
|--------|-------|--------|---------|
| Sarasota | Python | 🔄 In Progress | Date-based pagination solver |

## Known CMS Platforms
| Platform | Counties |
|----------|----------|
| Revize | Charlotte, Manatee |
| ASP.NET WebForms | Collier |
| Custom | DeSoto, Hendry, Lee |

## Important Patterns
- Charlotte and Manatee share the same Revize CMS — solver logic is very similar
- Collier uses ASP.NET ViewState postbacks for pagination
- DeSoto supports incremental scraping (only fetch new since last run)
- Hendry has a REST API that returns JSON — consider switching from browser to API
- Lee is primarily scraped via GAS; the Node.js code here is a backup trigger

## Field Alias Gems (from SCRAPING_GEMS_REPORT analysis)
- "Arrest Date" maps to `Booking_Date`
- "Inmate Name" and "Defendant" both map to `Full_Name`
- Bond amounts may be per-charge or total — check per county
- Some sites use "Release Date" to mean "Projected Release" not "Actual Release"

## Anti-Bot Notes
- Cloudflare sites (Charlotte, Manatee): need 10-20s JS wait
- No county currently uses reCAPTCHA
- Rate limiting: most sites tolerate 1 req/sec but throttle at 5 req/sec
- User-agent rotation helps with Revize sites
