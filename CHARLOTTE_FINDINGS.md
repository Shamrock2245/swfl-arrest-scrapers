# Charlotte County Scraper - Findings and Recommendations

## Discovery

Charlotte County Sheriff's Office uses a **Revize CMS** platform for their arrest database:

- **Main Page**: https://www.ccso.org/correctional_facility/local_arrest_database.php
- **Actual Database (iframe)**: https://inmates.charlottecountyfl.revize.com/bookings
- **Protection**: Cloudflare Turnstile CAPTCHA

## Current Status

The existing scraper (`scrapers/charlotte.js`) targets the wrong URL:
- ❌ **Configured URL**: `https://www.ccso.org/forms/arrestdb.cfm` (returns CAPTCHA)
- ✅ **Correct URL**: `https://inmates.charlottecountyfl.revize.com/bookings` (also has CAPTCHA, but better structure)

## Data Structure

The Revize platform shows arrests in a clean HTML table with:

| Field | Example |
|-------|---------|
| Booking # | 202506567 |
| Last Name | DUNCAN |
| First Name | BRYCE |
| Middle Initial | W |
| Charge | New Charge: 901.04 - Out of County Warrant |
| Arrest Date | 11-21-2025 |

Each booking number is a clickable link to detail pages:
- Example: `https://inmates.charlottecountyfl.revize.com/bookings/202506567`

## Challenges

1. **Cloudflare Turnstile CAPTCHA**: Blocks automated scraping
2. **No Public API**: Revize doesn't expose a public JSON API
3. **Stealth Mode Insufficient**: Current stealth plugin doesn't bypass Turnstile

## Recommended Solutions

### Option 1: Use Existing Data (Best for Now)
Since Charlotte County has CAPTCHA protection, we should:
1. **Prioritize other counties** without CAPTCHA (Sarasota, DeSoto, Manatee)
2. **Manual monitoring** for Charlotte County
3. **Revisit later** with advanced CAPTCHA solving

### Option 2: Advanced CAPTCHA Bypass (Future)
- Use services like 2Captcha or Anti-Captcha
- Implement browser fingerprint randomization
- Add residential proxy rotation
- Cost: ~$1-3 per 1000 CAPTCHAs

### Option 3: Alternative Data Source
- Check if Charlotte County provides **public records requests** for bulk data
- Look for **RSS feeds** or **email alerts**
- Contact IT department for **official API access**

### Option 4: Semi-Automated Approach
- Run scraper in **non-headless mode**
- **Manual CAPTCHA solving** when needed
- Scraper continues automatically after CAPTCHA is solved
- Good for low-frequency runs (once per day)

## Recommended Action

**Skip Charlotte County for now** and focus on:
1. ✅ Collier County (working)
2. ✅ Hendry County (working)
3. ✅ Lee County (working)
4. 🔄 Sarasota County (test next)
5. 🔄 DeSoto County (test next)
6. 🔍 Manatee County (find mobile API)
7. ⏸️ Charlotte County (CAPTCHA blocked - revisit later)

## Updated Configuration Needed

```json
{
  "charlotte": {
    "name": "Charlotte",
    "code": "CHARLOTTE",
    "sheetName": "Charlotte",
    "baseUrl": "https://inmates.charlottecountyfl.revize.com",
    "searchUrl": "https://inmates.charlottecountyfl.revize.com/bookings",
    "detailUrlPattern": "/bookings/{bookingId}",
    "daysBack": 3,
    "captcha": true,
    "status": "blocked",
    "fields": {
      "bookingNumber": "Booking #",
      "name": "First Name|Last Name",
      "charges": "Charge",
      "arrestDate": "Arrest Date"
    }
  }
}
```

## Next Steps

1. Update `config/counties.json` with correct Charlotte URLs
2. Mark Charlotte as "blocked" status
3. Move to Sarasota County testing
4. Document CAPTCHA bypass options for future implementation
