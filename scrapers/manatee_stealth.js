// scrapers/manatee_stealth.js
// Manatee County scraper with Puppeteer stealth mode and 34-column schema output

import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha, isCloudflareBlocked } from '../shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).manatee;

const LIST_URL = config.listUrl || 'https://manatee-sheriff.revize.com/bookings';
const BASE_URL = config.baseUrl || 'https://manatee-sheriff.revize.com';

/**
 * Main Manatee County scraper with stealth mode (34-column output)
 */
export async function runManateeStealth() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Manatee County Scraper (Stealth + 34-column)');
  console.log('═══════════════════════════════════════');

  let browser = null;

  try {
    // 1) Launch stealth browser
    console.log('🔒 Launching stealth browser...');
    browser = await newBrowser();
    const page = await newPage(browser);

    // 2) Navigate to bookings list page
    console.log(`📡 Navigating to ${LIST_URL}`);
    await navigateWithRetry(page, LIST_URL, { timeout: 45000 });

    // Check for blocking
    if (await isCloudflareBlocked(page)) {
      throw new Error('Blocked by Cloudflare');
    }
    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected');
    }

    // 3) Extract detail URLs from the list page
    const detailUrls = await extractDetailUrls(page);
    console.log(`📋 Found ${detailUrls.length} booking detail URLs`);

    if (detailUrls.length === 0) {
      await browser.close();
      await logIngestion('MANATEE', true, 0, startTime);
      console.log('ℹ️  No bookings found');
      return { success: true, count: 0 };
    }

    // 4) Fetch & parse each detail page
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Navigating to ${url}`);

      try {
        // Random delay to avoid rate limiting
        await randomDelay(800, 600);

        await navigateWithRetry(page, url, { timeout: 30000 });

        // Check for blocking
        if (await isCloudflareBlocked(page)) {
          console.warn('   ⚠️  Cloudflare detected, skipping...');
          continue;
        }

        const rawPairs = await extractDetailPairs(page, url);
        const record = normalizeRecord34(rawPairs, 'MANATEE', url);

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

    // 5) Write to Sheets
    if (records.length > 0) {
      const result = await upsertRecords34(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
    }

    await logIngestion('MANATEE', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    await browser.close();
    return { success: true, count: records.length };
  } catch (error) {
    console.error('❌ Fatal Manatee error:', error.message);
    if (browser) await browser.close();
    await logIngestion('MANATEE', false, 0, startTime, error.message);
    throw error;
  }
}

/**
 * Extract all detail URLs from the bookings list page using Puppeteer
 */
async function extractDetailUrls(page) {
  const urls = await page.$$eval('a[href*="/bookings/"]', (links, baseUrl) => {
    const uniqueUrls = new Set();
    
    links.forEach(link => {
      let href = link.getAttribute('href');
      if (!href) return;

      // Ignore links that are just /bookings (no ID)
      if (/\/bookings\/?$/i.test(href)) return;

      if (!href.startsWith('http')) {
        href = baseUrl.replace(/\/$/, '') + (href.startsWith('/') ? href : `/${href}`);
      }
      uniqueUrls.add(href);
    });

    return Array.from(uniqueUrls);
  }, BASE_URL);

  return urls.slice(0, 50); // safety cap
}

/**
 * Extract label/value pairs from a detail page using Puppeteer
 */
async function extractDetailPairs(page, sourceUrl) {
  const data = {};

  // Extract table-based data
  const tableData = await page.$$eval('table tr', rows => {
    const result = {};
    rows.forEach(row => {
      const tds = row.querySelectorAll('td');
      if (tds.length >= 2) {
        const label = tds[0].textContent.trim();
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
        const label = dt.textContent.trim();
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
    'img[src*="mug"], img[src*="photo"], img[src*="mugshots"]',
    (img, baseUrl) => {
      let src = img.getAttribute('src');
      if (!src) return null;
      if (!src.startsWith('http')) {
        src = baseUrl.replace(/\/$/, '') + (src.startsWith('/') ? src : `/${src}`);
      }
      return src;
    },
    BASE_URL
  ).catch(() => null);

  if (mugshot) {
    data['mugshot'] = mugshot;
  }

  data['source_url'] = sourceUrl;
  data['detail_url'] = sourceUrl;

  return data;
}

// Allow direct execution via `node scrapers/manatee_stealth.js`
if (import.meta.url === `file://${process.argv[1]}`) {
  runManateeStealth().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runManateeStealth;
