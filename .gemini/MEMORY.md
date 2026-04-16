# 🧠 MEMORY — Learned Patterns & County Quirks

> **What I've learned from past failures and successes. Read this before touching a county.**

---

## County-Specific Knowledge

### Charlotte
- ColdFusion backend — date formats vary between `MM/DD/YYYY` and `YYYY-MM-DD`
- Multiple search result pages; must paginate
- Stable since Wave 0, rarely changes

### Collier
- Requires clicking a disclaimer/acceptance before accessing data
- Previously used GAS scraper; migrated to requests+BS4 in April 2026
- Occasionally returns stale data — add timestamp verification

### DeSoto
- SmartCOP/SmartWEB platform — this is the template for 13 other counties
- ASP.NET ViewState: let the browser handle it (Puppeteer/DrissionPage)
- Session timeout after ~5 minutes — refresh if scraping takes longer

### Hendry
- Very low volume county (1-5 arrests/day)
- API-based data access (JSON endpoint)
- Runs every 2h — no need for more frequent scraping

### Highlands
- Interactive search form requiring date range input
- Fixed in April 2026 — was returning 0 records due to form submission change

### Hillsborough
- ASP.NET with ViewState — high volume county
- `requests+BS4` works because the data is in static HTML tables
- Every 20 minutes (highest frequency) due to volume

### Indian River
- Interactive search form — requires submitting date range
- Fixed in April 2026 — selector drift on search results table

### Manatee
- Arrest inquiry form — must submit form to get results
- DrissionPage required for JavaScript form handling

### Orange
- Previously had PDF-based roster AND web scraping
- Now primarily web scraping via DrissionPage
- High volume — runs every 30 minutes

### Osceola
- Corrections report search form
- Uses **Playwright** (not DrissionPage) due to specific page interaction needs
- Fixed in April 2026 — updated selectors

### Palm Beach
- Very high volume county
- Occasional timeouts during peak hours (morning arraignments)
- If timeout occurs, retry with extended timeout (60s)

### Sarasota
- **Cloudflare strict mode** — DrissionPage is required, headful preferred
- Longest-running stealth challenge in the network
- If blocked, escalate per Playbook 1 in ERRORS_AND_RECOVERY.md

---

## System-Wide Patterns

### What Always Breaks
1. **ASP.NET ViewState changes** — .NET sites regenerate ViewState on updates
2. **CSS class name changes** — Sites using build tools (webpack, etc.) randomize class names
3. **CAPTCHA additions** — Counties add CAPTCHA when they notice scraping
4. **Certificate renewals** — SSL cert changes can break requests sessions
5. **Form structure changes** — Search forms add/remove fields

### What Always Works
1. **requests+BS4 on simple HTML** — Static pages almost never break
2. **DrissionPage on JS-heavy sites** — Real browser fingerprint bypasses most protections
3. **JSON API endpoints** — When a county has one, it's the most stable source
4. **Stable selector patterns** — IDs are more reliable than class names
5. **Pagination via URL params** — `?page=2` is more reliable than clicking "Next"

### Recovery Patterns That Work
1. **Headless → headful** — Fixes ~60% of Cloudflare blocks
2. **Add 5-10s delay** — Fixes ~80% of rate limit issues
3. **Update user-agent** — Fixes ~30% of random 403s
4. **Save fixture → compare** — Always the first step for selector drift

---

## Anti-Bot Intelligence

### Known Anti-Bot Behaviors by Platform
| Platform | Common Blocks | Bypass Strategy |
|---|---|---|
| SmartCOP/SmartWEB | Minimal | Standard requests/Puppeteer |
| Cloudflare JS Challenge | UA + timing checks | DrissionPage headful + delays |
| ASP.NET WebForms | Session validation | Let real browser handle ViewState |
| Tyler Tech/New World | Slow rendering | DrissionPage + 60s timeouts |
| ColdFusion | IP-based rate limit | Stagger requests, 5s+ delays |

### GitHub Actions Runner IPs
- GitHub shared runners rotate IPs, which helps avoid persistent blocks
- However, ALL repos share the same runner pool — other scrapers may cause blocks
- Self-hosted runners (Hetzner) have fixed IPs — may need proxy for sensitive counties

---

## Lessons Learned

| Date | Lesson | Impact |
|------|--------|--------|
| 2026-04-14 | Collier can be scraped with requests+BS4 (no DrissionPage needed) | Faster, less resource-heavy |
| 2026-04-14 | Indian River search form requires explicit date formatting | Was returning 0 records |
| 2026-04-14 | Osceola works better with Playwright than DrissionPage | Switched engines |
| 2026-03 | SmartCOP pattern can be reused across 13+ counties | Major expansion accelerator |
| 2026-03 | Cloudflare blocks increase on weekday mornings (court days) | Schedule sensitive counties off-peak |
