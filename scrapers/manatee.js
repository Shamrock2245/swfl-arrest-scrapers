// scrapers/manatee.js
// Manatee County scraper with 34-column schema output (Puppeteer version)

import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import 'dotenv/config';
import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
import { newBrowser, newPage, navigateWithRetry, randomDelay } from '../shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).manatee;

puppeteerExtra.use(StealthPlugin());

const LIST_URL = config.listUrl || 'https://manatee-sheriff.revize.com/bookings';
const BASE_URL = config.baseUrl || 'https://manatee-sheriff.revize.com';

/**
 * Main Manatee County scraper (34-column output)
 */
export async function runManatee() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Manatee County Scraper (Puppeteer)');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // 1) Fetch main bookings page
    console.log(`📡 Navigating to ${LIST_URL}`);
    await navigateWithRetry(page, LIST_URL);
    await randomDelay(page, 2000, 4000);

    // 2) Extract detail URLs
    const detailUrls = await page.evaluate((baseUrl) => {
      const links = Array.from(document.querySelectorAll('a[href*="/bookings/"]'));
      const urls = new Set();

      links.forEach(link => {
        let href = link.getAttribute('href');
        if (!href) return;

        // Ignore links that are just /bookings (no ID)
        if (/\/bookings\/?$/i.test(href)) return;

        if (!href.startsWith('http')) {
          href = baseUrl.replace(/\/$/, '') + (href.startsWith('/') ? href : `/${href}`);
        }
        urls.add(href);
      });

      return [...urls].slice(0, 50); // safety cap
    }, BASE_URL);

    console.log(`📋 Found ${detailUrls.length} booking detail URLs`);

    if (detailUrls.length === 0) {
      await logIngestion('MANATEE', true, 0, startTime);
      console.log('ℹ️  No bookings found');
      await browser.close();
      return { success: true, count: 0 };
    }

    // 3) Visit each detail page
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Visiting ${url}`);

      try {
        await navigateWithRetry(page, url);
        await randomDelay(page, 1000, 2500);

        const rawPairs = await page.evaluate((sourceUrl) => {
          const data = {};

          // Generic table-based layout
          const rows = document.querySelectorAll('table tr');
          rows.forEach(row => {
            const tds = row.querySelectorAll('td');
            if (tds.length >= 2) {
              const label = tds[0].innerText.trim();
              const value = tds[1].innerText.trim();
              if (label && value) data[label] = value;
            }
          });

          // DL structure
          const dls = document.querySelectorAll('dl');
          dls.forEach(dl => {
            const dts = dl.querySelectorAll('dt');
            dts.forEach(dt => {
              const label = dt.innerText.trim();
              let next = dt.nextElementSibling;
              if (next && next.tagName === 'DD') {
                const value = next.innerText.trim();
                if (label && value) data[label] = value;
              }
            });
          });

          // Mugshot
          const img = document.querySelector('img[src*="mug"], img[src*="photo"], img[src*="mugshots"]');
          if (img) {
            data['mugshot'] = img.src;
          }

          data['source_url'] = sourceUrl;
          data['detail_url'] = sourceUrl;
          return data;
        }, url);

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

    // 4) Write to Sheets
    if (records.length > 0) {
      const result = await upsertRecords34(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
    }

    await logIngestion('MANATEE', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal Manatee error:', error.message);
    await logIngestion('MANATEE', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  runManatee().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runManatee;
