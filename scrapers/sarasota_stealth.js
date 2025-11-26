// scrapers/sarasota_stealth.js
// Sarasota County scraper with Puppeteer stealth mode, date-based search, and 34-column schema output

import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha, isCloudflareBlocked, waitForCloudflare, humanScroll, humanType, humanClick } from '../shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).sarasota;

const MAIN_URL = 'https://www.sarasotasheriff.org/arrest-reports/index.php';
const IFRAME_URL = 'https://cms.revize.com/revize/apps/sarasota/index.php';

/**
 * Main Sarasota County scraper with stealth mode and date search (34-column output)
 * @param {string} arrestDate - Date to search in MM/DD/YYYY format (defaults to today)
 */
export async function runSarasotaStealth(arrestDate = null) {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Sarasota County Scraper (Stealth + Date Search + 34-column)');
  console.log('═══════════════════════════════════════');

  // Default to today's date if not provided
  if (!arrestDate) {
    const today = new Date();
    arrestDate = `${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getDate().toString().padStart(2, '0')}/${today.getFullYear()}`;
  }
  console.log(`📅 Searching for arrests on: ${arrestDate}`);

  let browser = null;

  try {
    // 1) Launch stealth browser
    console.log('🔒 Launching stealth browser...');
    browser = await newBrowser();
    const page = await newPage(browser);

    // 2) Navigate to main page to find iframe
    console.log(`📡 Loading main page: ${MAIN_URL}`);
    await navigateWithRetry(page, MAIN_URL, { timeout: 45000 });
    await randomDelay(1000, 400);

    // 3) Find iframe URL
    const iframeUrl = await page.evaluate(() => {
      const iframe = document.querySelector('iframe[src*="cms.revize.com/revize/apps/sarasota"]');
      return iframe ? iframe.src : null;
    });

    if (!iframeUrl) {
      throw new Error('Could not find arrest search iframe');
    }

    console.log(`➡️  Navigating to arrest search form: ${iframeUrl}`);
    await navigateWithRetry(page, iframeUrl, { timeout: 45000 });
    await randomDelay(3000, 1000);
    
    // Simulate human behavior
    await humanScroll(page, 200);
    await randomDelay(1000, 500);

    // Check for blocking and wait if needed
    if (await isCloudflareBlocked(page)) {
      console.log('⚠️  Cloudflare detected, waiting for challenge to resolve...');
      await waitForCloudflare(page, 30000);
    }

    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected');
    }

    // 4) Fill in date search form
    console.log(`🔍 Filling arrest date search form...`);
    
    // Click on "Arrest Date" tab if not already active
    const arrestDateTab = await page.$('a:has-text("Arrest Date")').catch(() => null);
    if (arrestDateTab) {
      await arrestDateTab.click();
      await randomDelay(500, 200);
    }

    // Find and fill the date input field
    const dateInput = await page.$('input[name="arrest_date"], input[type="text"][placeholder*="date"], input#arrest_date');
    if (!dateInput) {
      throw new Error('Could not find arrest date input field');
    }

    await dateInput.click({ clickCount: 3 }); // Select all existing text
    await dateInput.type(arrestDate);
    await randomDelay(500, 200);

    // Click search button
    const searchButton = await page.$('button:has-text("Search"), input[type="submit"][value*="Search"]');
    if (!searchButton) {
      throw new Error('Could not find search button');
    }

    console.log(`🔎 Submitting search for ${arrestDate}...`);
    await searchButton.click();
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
    await randomDelay(2000, 500);

    // 5) Extract detail URLs from search results
    const detailUrls = await extractDetailUrls(page);
    console.log(`📋 Found ${detailUrls.length} arrest records for ${arrestDate}`);

    if (detailUrls.length === 0) {
      await browser.close();
      await logIngestion('SARASOTA', true, 0, startTime);
      console.log('ℹ️  No arrests found for this date');
      return { success: true, count: 0 };
    }

    // 6) Fetch & parse each detail page
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Navigating to ${url}`);

      try {
        // Longer delay to appear human-like
        await randomDelay(3000, 2000);
        await navigateWithRetry(page, url, { timeout: 30000 });

        // Check for blocking and wait if needed
        if (await isCloudflareBlocked(page)) {
          console.warn('   ⚠️  Cloudflare detected, waiting...');
          try {
            await waitForCloudflare(page, 20000);
          } catch (err) {
            console.warn('   ⚠️  Still blocked, skipping...');
            continue;
          }
        }
        
        // Simulate human behavior
        await humanScroll(page, 150);
        await randomDelay(500, 300);

        const rawPairs = await extractDetailPairs(page, url);
        const record = normalizeRecord34(rawPairs, 'SARASOTA', url);

        if (record.Booking_Number) {
          records.push(record);
          console.log(`   ✅ ${record.Full_Name} (${record.Booking_Number})`);
        } else {
          console.log('   ⚠️  Missing Booking_Number after normalization, skipping');
        }
      } catch (err) {
        console.error(`   ⚠️  Error processing ${url}: ${err.message}`);
      }
    }

    console.log(`\n📊 Parsed ${records.length} valid records`);

    // 7) Write to Sheets
    if (records.length > 0) {
      const result = await upsertRecords34(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
    }

    await logIngestion('SARASOTA', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    await browser.close();
    return { success: true, count: records.length };
  } catch (error) {
    console.error('❌ Fatal Sarasota error:', error.message);
    if (browser) await browser.close();
    await logIngestion('SARASOTA', false, 0, startTime, error.message);
    throw error;
  }
}

/**
 * Run Sarasota scraper for the last N days
 * @param {number} daysBack - Number of days to go back (default: 3)
 */
export async function runSarasotaMultipleDays(daysBack = 3) {
  console.log(`🗓️  Running Sarasota scraper for the last ${daysBack} days...`);
  
  const results = [];
  for (let i = 0; i < daysBack; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}/${date.getFullYear()}`;
    
    try {
      const result = await runSarasotaStealth(dateStr);
      results.push({ date: dateStr, ...result });
    } catch (err) {
      console.error(`❌ Failed to scrape ${dateStr}: ${err.message}`);
      results.push({ date: dateStr, success: false, count: 0 });
    }
  }

  const totalCount = results.reduce((sum, r) => sum + r.count, 0);
  console.log(`\n📊 Total records across ${daysBack} days: ${totalCount}`);
  
  return results;
}

/**
 * Extract all detail URLs from the search results page
 */
async function extractDetailUrls(page) {
  const urls = await page.$$eval('a[href*="viewInmate.php"], a[href*="detail.php"]', (links, baseUrl) => {
    const uniqueUrls = new Set();
    
    links.forEach(link => {
      let href = link.getAttribute('href');
      if (!href) return;

      if (!href.startsWith('http')) {
        // Get the base URL from the current page
        const currentUrl = window.location.href;
        const urlObj = new URL(currentUrl);
        const base = `${urlObj.protocol}//${urlObj.host}${urlObj.pathname.substring(0, urlObj.pathname.lastIndexOf('/') + 1)}`;
        href = base + href;
      }
      uniqueUrls.add(href);
    });

    return Array.from(uniqueUrls);
  }, IFRAME_URL);

  return urls.slice(0, 100); // safety cap
}

/**
 * Extract label/value pairs from a detail page
 */
async function extractDetailPairs(page, sourceUrl) {
  const data = {};

  // Extract table-based data
  const tableData = await page.$$eval('table tr', rows => {
    const result = {};
    rows.forEach(row => {
      const tds = row.querySelectorAll('td');
      if (tds.length >= 2) {
        const label = tds[0].textContent.trim().replace(/:$/, '');
        const value = tds[1].textContent.trim();
        if (label && value) result[label] = value;
      }
    });
    return result;
  });

  Object.assign(data, tableData);

  // Extract dl/dt/dd structure
  const dlData = await page.$$eval('dl', dls => {
    const result = {};
    dls.forEach(dl => {
      const dts = dl.querySelectorAll('dt');
      dts.forEach(dt => {
        const label = dt.textContent.trim().replace(/:$/, '');
        const dd = dt.nextElementSibling;
        if (dd && dd.tagName === 'DD') {
          const value = dd.textContent.trim();
          if (label && value) result[label] = value;
        }
      });
    });
    return result;
  });

  Object.assign(data, dlData);

  // Extract mugshot
  const mugshot = await page.$eval(
    'img[src*="mug"], img[src*="photo"], img[alt*="mugshot"], img[alt*="photo"]',
    (img) => {
      let src = img.getAttribute('src');
      if (!src) return null;
      if (!src.startsWith('http')) {
        const currentUrl = window.location.href;
        const urlObj = new URL(currentUrl);
        const base = `${urlObj.protocol}//${urlObj.host}`;
        src = base + (src.startsWith('/') ? src : `/${src}`);
      }
      return src;
    }
  ).catch(() => null);

  if (mugshot) {
    data['mugshot'] = mugshot;
  }

  data['source_url'] = sourceUrl;
  data['detail_url'] = sourceUrl;

  return data;
}

// Allow direct execution via `node scrapers/sarasota_stealth.js [date]`
if (import.meta.url === `file://${process.argv[1]}`) {
  const arrestDate = process.argv[2]; // Optional: pass date as MM/DD/YYYY
  
  if (process.argv[2] === '--multi-day') {
    const daysBack = parseInt(process.argv[3]) || 3;
    runSarasotaMultipleDays(daysBack).catch(err => {
      console.error('Fatal error:', err);
      process.exit(1);
    });
  } else {
    runSarasotaStealth(arrestDate).catch(err => {
      console.error('Fatal error:', err);
      process.exit(1);
    });
  }
}

export default runSarasotaStealth;
