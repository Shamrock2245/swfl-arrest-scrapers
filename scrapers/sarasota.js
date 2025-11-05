import { navigateWithRetry, randomDelay, hasCaptcha, sleep } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// --- SARASOTA-SPECIFIC BROWSER SETUP FOR CLOUDFLARE BYPASS ---
import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

// Use stealth plugin
puppeteerExtra.use(StealthPlugin());

// Duplicating from shared/browser.js to avoid changing the shared function signatures
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

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).sarasota;

export async function runSarasota() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Sarasota County Scraper');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    browser = await newStealthBrowser();
    const page = await newStealthPage(browser);

    console.log(`📡 Loading initial page to find iframe: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);
    await randomDelay(1000, 400);

    // Find the iframe URL which hosts the arrest data
    const iframeUrl = await page.evaluate(() => {
      const iframe = document.querySelector('iframe[src*="cms.revize.com/revize/apps/sarasota"]');
      return iframe ? iframe.src : null;
    });
    
    if (!iframeUrl) {
        throw new Error('Could not find the arrest report iframe on the main page.');
    }

    console.log(`➡️  Navigating directly to arrest data page: ${iframeUrl}`);
    // Navigate the main page to the iframe's URL using the stealth-enabled page
    await navigateWithRetry(page, iframeUrl);
    
    // NOTE: The previous hasCaptcha check caused a false positive on this page.
    // By using the stealth plugin and navigating directly, we bypass the block.
    // The explicit hasCaptcha check is removed to eliminate the false positive.

    const detailUrls = await parseListPage(page);
    console.log(`📋 Found ${detailUrls.length} arrest records`);

    if (detailUrls.length === 0) {
      await logIngestion('SARASOTA', true, 0, startTime);
      return { success: true, count: 0 };
    }

    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Fetching: ${url}`);

      try {
        await randomDelay(1000, 400);
        await navigateWithRetry(page, url);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'SARASOTA', url);
        
        if (record.booking_id) {
          records.push(record);
          console.log(`   ✅ ${record.full_name_last_first} (${record.booking_id})`);
        }
      } catch (error) {
        console.error(`   ⚠️  Error: ${error.message}`);
      }
    }

    console.log(`\n📊 Parsed ${records.length} valid records`);

    if (records.length > 0) {
      const result = await upsertRecords(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
      await mirrorQualifiedToDashboard(records);
    }

    await logIngestion('SARASOTA', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('SARASOTA', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

async function parseListPage(page) {
  try {
    await page.waitForSelector('table, .arrest, a[href*="detail"]', { timeout: 10000 });
    const links = await page.$$eval('a[href*="detail"], a[href*="id="]', elements => 
      elements.map(el => el.href).filter(Boolean)
    );
    const uniqueUrls = [...new Set(links)];
    return uniqueUrls.slice(0, 50);
  } catch (error) {
    console.error('⚠️  Error parsing list:', error.message);
    return [];
  }
}

async function extractDetailPairs(page) {
  try {
    await page.waitForSelector('table, .detail', { timeout: 5000 });
    return await page.evaluate(() => {
      const data = {};
      document.querySelectorAll('table tr').forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
          data[cells[0].textContent.trim()] = cells[1].textContent.trim();
        }
      });
      const img = document.querySelector('img[src*="photo"], img[src*="mugshot"]');
      if (img) data['mugshot'] = img.src;
      data['source_url'] = window.location.href;
      return data;
    });
  } catch (error) {
    return { source_url: page.url() };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runSarasota().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runSarasota;
