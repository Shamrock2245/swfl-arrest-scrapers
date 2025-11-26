# Stealth Scraper Implementation

## Overview

All SWFL arrest scrapers now use **Puppeteer with stealth mode** to avoid detection and ensure reliable data collection from county jail websites.

---

## What Changed

### 1. **Updated `shared/browser.js`**
- Now uses `puppeteer-extra` instead of basic `puppeteer`
- Applies `puppeteer-extra-plugin-stealth` for anti-detection
- Removes automation flags and mocks browser properties
- Adds randomized user agents and realistic headers

### 2. **Created `scrapers/manatee_stealth.js`**
- Manatee County scraper using Puppeteer stealth mode
- Outputs to 34-column Google Sheets format
- Includes Cloudflare and CAPTCHA detection
- Random delays between requests to avoid rate limiting

---

## Stealth Features

### Anti-Detection Measures

1. **Stealth Plugin**
   - Removes `navigator.webdriver` flag
   - Mocks Chrome plugins and extensions
   - Fixes WebGL vendor/renderer
   - Patches navigator properties

2. **Randomized User Agents**
   - Rotates between macOS, Windows, and Linux Chrome user agents
   - Version 120.0.0.0 (current stable)

3. **Realistic Headers**
   - Accept-Language, Accept-Encoding, DNT
   - Connection: keep-alive
   - Upgrade-Insecure-Requests

4. **Browser Arguments**
   - `--disable-blink-features=AutomationControlled`
   - `--disable-features=IsolateOrigins,site-per-process`
   - `--disable-web-security`

5. **Random Delays**
   - 800ms base delay + 600ms jitter between requests
   - Prevents rate limiting and looks more human

6. **Cloudflare & CAPTCHA Detection**
   - Detects "Just a moment..." Cloudflare challenges
   - Detects reCAPTCHA and other CAPTCHA systems
   - Skips blocked pages gracefully

---

## Usage

### Run Manatee Stealth Scraper

```bash
node scrapers/manatee_stealth.js
```

### Expected Output

```
═══════════════════════════════════════
🚦 Starting Manatee County Scraper (Stealth + 34-column)
═══════════════════════════════════════
🔒 Launching stealth browser...
📡 Navigating to https://manatee-sheriff.revize.com/bookings
📋 Found 25 booking detail URLs
🔍 [1/25] Navigating to https://manatee-sheriff.revize.com/bookings/12345
   ✅ SMITH, JOHN (12345)
🔍 [2/25] Navigating to https://manatee-sheriff.revize.com/bookings/12346
   ✅ DOE, JANE (12346)
...
📊 Parsed 25 valid records
✅ Manatee: inserted 20, updated 5
📝 Logged ingestion: MANATEE - SUCCESS
⏱️  Total execution time: 65s
═══════════════════════════════════════
```

---

## Integration with Other Scrapers

All county scrapers should be updated to use the stealth browser module:

```javascript
import { newBrowser, newPage, navigateWithRetry, randomDelay } from '../shared/browser.js';

export async function runCountyScraper() {
  const browser = await newBrowser();  // Stealth enabled
  const page = await newPage(browser);  // Random UA + headers
  
  await navigateWithRetry(page, url);  // Retry logic
  await randomDelay();  // Human-like delays
  
  // ... scraping logic ...
  
  await browser.close();
}
```

---

## Dependencies

Already installed in `package.json`:

```json
{
  "dependencies": {
    "puppeteer": "^21.6.1",
    "puppeteer-extra": "^3.3.6",
    "puppeteer-extra-plugin-stealth": "^2.11.2"
  }
}
```

No additional installation required!

---

## Troubleshooting

### Issue: "Blocked by Cloudflare"
**Solution**: 
- The scraper will detect and skip Cloudflare-protected pages
- Consider adding a longer delay before retrying
- Check if the website has changed its protection

### Issue: "CAPTCHA detected"
**Solution**:
- The scraper will detect and skip CAPTCHA pages
- Manual intervention may be required
- Consider using a CAPTCHA solving service (2captcha, Anti-Captcha)

### Issue: "Navigation timeout"
**Solution**:
- Increase timeout in `navigateWithRetry` options
- Check if the website is down or slow
- Verify network connectivity

### Issue: "Too many requests"
**Solution**:
- Increase `randomDelay` base time (e.g., 1500ms)
- Add longer delays between detail page fetches
- Reduce the number of concurrent requests

---

## Performance

### Stealth vs. Basic Fetch

| Method | Speed | Reliability | Detection Risk |
|--------|-------|-------------|----------------|
| Basic `fetch()` | Fast (5-10s) | Low | **High** |
| Puppeteer (no stealth) | Medium (30-45s) | Medium | **Medium** |
| Puppeteer + Stealth | Slower (60-90s) | **High** | **Low** |

**Recommendation**: Use stealth mode for production scrapers to ensure long-term reliability.

---

## Future Enhancements

1. **Residential Proxies**
   - Rotate IP addresses to avoid IP-based blocking
   - Use services like Bright Data, Oxylabs, or Smartproxy

2. **CAPTCHA Solving**
   - Integrate 2captcha or Anti-Captcha API
   - Automatically solve CAPTCHAs when detected

3. **Headless Detection Evasion**
   - Use `puppeteer-extra-plugin-anonymize-ua`
   - Add canvas fingerprint randomization

4. **Session Management**
   - Reuse browser sessions across runs
   - Maintain cookies for authenticated scraping

5. **Distributed Scraping**
   - Run scrapers on multiple machines
   - Use message queues (RabbitMQ, Redis) for coordination

---

## Testing

### Test Stealth Detection

Visit https://bot.sannysoft.com/ with the stealth browser:

```javascript
import { newBrowser, newPage } from './shared/browser.js';

const browser = await newBrowser();
const page = await newPage(browser);
await page.goto('https://bot.sannysoft.com/');
await page.screenshot({ path: 'stealth-test.png' });
await browser.close();
```

**Expected**: Most tests should show green checkmarks (not detected as bot).

---

## Best Practices

1. **Always use random delays** between requests
2. **Detect and handle Cloudflare/CAPTCHA** gracefully
3. **Rotate user agents** for each session
4. **Monitor for detection** and adjust stealth settings
5. **Respect rate limits** to avoid IP bans
6. **Log all errors** for debugging and monitoring

---

## Support

For issues or questions:
- Check the main README.md
- Review MANATEE_34COLUMN_README.md
- Check GitHub issues: https://github.com/Shamrock2245/swfl-arrest-scrapers/issues
