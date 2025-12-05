// scrapers/manatee34.js
// Manatee County scraper with 34-column schema output

import * as cheerio from 'cheerio';
import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
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
 * Main Manatee County scraper (34-column output)
 */
export async function runManatee34() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Manatee County Scraper (34-column)');
  console.log('═══════════════════════════════════════');

  try {
    // 1) Fetch main bookings page
    console.log(`📡 GET ${LIST_URL}`);
    const listHtml = await fetchText(LIST_URL);

    // 2) Extract detail URLs from the list HTML
    const detailUrls = extractDetailUrls(listHtml);
    console.log(`📋 Found ${detailUrls.length} booking detail URLs`);

    if (detailUrls.length === 0) {
      await logIngestion('MANATEE', true, 0, startTime);
      console.log('ℹ️  No bookings found');
      return { success: true, count: 0 };
    }

    // 3) Fetch & parse each detail page
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] GET ${url}`);

      try {
        const html = await fetchText(url);
        const rawPairs = extractDetailPairs(html, url);
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
  }
}

/**
 * Simple helper for GET text with basic retry
 */
async function fetchText(url, retries = 3) {
  let lastErr;
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, {
        headers: {
          'User-Agent':
            'Mozilla/5.0 (compatible; ShamrockScraper/1.0; +https://shamrockbailbonds.biz)',
          'Accept': 'text/html,application/xhtml+xml'
        },
        redirect: 'follow'
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.text();
    } catch (err) {
      lastErr = err;
      console.warn(`   ⚠️  Fetch failed (${attempt}/${retries}) for ${url}: ${err.message}`);
      await new Promise(r => setTimeout(r, 1000 * attempt));
    }
  }
  throw lastErr;
}

/**
 * Extract all detail URLs from the bookings list HTML
 * Manatee pattern: /bookings/BOOKING_ID
 */
function extractDetailUrls(html) {
  const $ = cheerio.load(html);
  const urls = new Set();

  $('a[href*="/bookings/"]').each((_, el) => {
    let href = $(el).attr('href');
    if (!href) return;

    // Ignore links that are just /bookings (no ID)
    if (/\/bookings\/?$/i.test(href)) return;

    if (!href.startsWith('http')) {
      href = BASE_URL.replace(/\/$/, '') + (href.startsWith('/') ? href : `/${href}`);
    }
    urls.add(href);
  });

  return [...urls].slice(0, 50); // safety cap
}

/**
 * Extract label/value pairs from a detail HTML page
 * to feed into normalizeRecord34
 */
function extractDetailPairs(html, sourceUrl) {
  const $ = cheerio.load(html);
  const data = {};

  // Generic table-based layout: first <td> = label, second = value
  $('table tr').each((_, row) => {
    const tds = $(row).find('td');
    if (tds.length >= 2) {
      const label = $(tds[0]).text().trim();
      const value = $(tds[1]).text().trim();
      if (label && value) data[label] = value;
    }
  });

  // Also try dl/dt/dd structure
  $('dl').each((_, dl) => {
    $(dl).find('dt').each((idx, dt) => {
      const label = $(dt).text().trim();
      const dd = $(dt).next('dd');
      if (dd.length) {
        const value = dd.text().trim();
        if (label && value) data[label] = value;
      }
    });
  });

  // Mugshot: either explicit <img> or we can construct from booking id later
  let mug = $('img[src*="mug"], img[src*="photo"], img[src*="mugshots"]').attr('src');
  if (mug) {
    if (!mug.startsWith('http')) {
      mug = BASE_URL.replace(/\/$/, '') + (mug.startsWith('/') ? mug : `/${mug}`);
    }
    data['mugshot'] = mug;
  }

  data['source_url'] = sourceUrl;
  data['detail_url'] = sourceUrl;

  return data;
}

// Allow direct execution via `node scrapers/manatee34.js`
if (import.meta.url === `file://${process.argv[1]}`) {
  runManatee34().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runManatee34;
