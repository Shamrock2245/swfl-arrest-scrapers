import { navigateWithRetry, randomDelay, hasCaptcha, isCloudflareBlocked } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// --- CHARLOTTE-SPECIFIC BROWSER SETUP FOR CLOUDFLARE BYPASS (STEALTH) ---
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Use stealth plugin
puppeteerExtra.use(StealthPlugin());

// The shared/browser.js file has these arrays, we define them locally for the stealth browser setup
const USER_AGENTS = [
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
];

async function newStealthBrowser() {
  const browser = await puppeteerExtra.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-blink-features=AutomationControlled',
      '--disable-features=IsolateOrigins,site-per-process'
    ],
    defaultViewport: {
      width: 1366,
      height: 900
    }
  });
  return browser;
}

async function newStealthPage(browser) {
  const page = await browser.newPage();
  
  const userAgent = USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
  await page.setUserAgent(userAgent);

  await page.setExtraHTTPHeaders({
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
  });

  await page.evaluateOnNewDocument(() => {
    Object.defineProperty(navigator, 'webdriver', {
      get: () => false
    });
  });

  return page;
}
// -----------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).charlotte;

/**
 * Main Charlotte County scraper
 */
export async function runCharlotte() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Charlotte County Scraper (Stealth Mode)');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    // Use stealth browser
    browser = await newStealthBrowser();
    const page = await newStealthPage(browser);

    // Navigate to search page
    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);

    // Enhanced Check for Cloudflare - be patient/stealthy
    if (await isCloudflareBlocked(page)) {
      console.log('⚠️  Cloudflare protection detected - waiting up to 15s for stealth mode to resolve...');
      
      // Wait longer for the stealth plugin to resolve Cloudflare (15s total wait)
      await page.waitForTimeout(10000); 
      
      if (await isCloudflareBlocked(page)) {
        console.log('⚠️  Cloudflare protection persists after long wait. Retrying navigation...');
        // Try navigating again with the same stealth page
        await navigateWithRetry(page, config.searchUrl); 
        await page.waitForTimeout(5000);

        if (await isCloudflareBlocked(page)) {
          throw new Error('Cloudflare blocked - Cannot bypass stealthily, stopping run.');
        }
      }
    }

    // Check for CAPTCHA
    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected - cannot proceed');
    }

    // Parse arrests from the page
    const detailUrls = await parseListPage(page);
    console.log(`📋 Found ${detailUrls.length} arrest records`);

    if (detailUrls.length === 0) {
      console.log('ℹ️  No arrests found');
      await logIngestion('CHARLOTTE', true, 0, startTime);
      return { success: true, count: 0 };
    }

    // Fetch details
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Fetching: ${url}`);

      try {
        // Enforce a minimum delay for discretion (satisfies "scrape one entry every few minutes" approach when run in cron)
        await randomDelay(2000, 1000); 
        await navigateWithRetry(page, url);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'CHARLOTTE', url);
        
        if (record.booking_id) {
          records.push(record);
          console.log(`   ✅ ${record.full_name_last_first} (${record.booking_id})`);
        }
      } catch (error) {
        console.error(`   ⚠️  Error processing ${url}: ${error.message}`);
      }
    }

    console.log(`\n📊 Parsed ${records.length} valid records`);

    // Write to sheets
    if (records.length > 0) {
      const result = await upsertRecords(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);

      await mirrorQualifiedToDashboard(records);
    }

    await logIngestion('CHARLOTTE', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('CHARLOTTE', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Parse list page (CFM format)
 */
async function parseListPage(page) {
  try {
    await page.waitForSelector('table, a[href*="arrestdb"]', { timeout: 10000 });

    const links = await page.$$eval('a[href*="arrestdb"], a[href*="id="]', elements => 
      elements.map(el => el.href).filter(Boolean)
    );

    const baseUrl = config.baseUrl;
    const uniqueUrls = [...new Set(links.map(url => {
      if (url.startsWith('http')) return url;
      return baseUrl + (url.startsWith('/') ? url : '/' + url);
    }))];

    return uniqueUrls.slice(0, 50); // Limit to prevent timeouts
  } catch (error) {
    console.error('⚠️  Error parsing list page:', error.message);
    return [];
  }
}

/**
 * Extract data from detail page
 */
async function extractDetailPairs(page) {
  try {
    await page.waitForSelector('table', { timeout: 5000 });

    const pairs = await page.evaluate(() => {
      const data = {};

      // CFM pages typically use tables with label: value format
      document.querySelectorAll('table tr').forEach(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        
        // Look for label:value pattern
        cells.forEach((cell, idx) => {
          const text = cell.textContent.trim();
          if (text.includes(':')) {
            const [label, ...valueParts] = text.split(':');
            data[label.trim()] = valueParts.join(':').trim();
          } else if (idx > 0 && cells[idx - 1]) {
            // Previous cell might be label
            const prevText = cells[idx - 1].textContent.trim();
            if (prevText && text && text.length > 1) {
              data[prevText] = text;
            }
          }
        });
      });

      // Look for mugshot
      const img = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[src*="image"]');
      if (img) {
        data['mugshot'] = img.src;
      }

      data['source_url'] = window.location.href;

      return data;
    });

    return pairs;
  } catch (error) {
    console.error('⚠️  Error extracting detail pairs:', error.message);
    return { source_url: page.url() };
  }
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  runCharlotte().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runCharlotte;
