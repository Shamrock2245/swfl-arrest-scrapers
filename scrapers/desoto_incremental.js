import 'dotenv/config';
import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).desoto;
const DATA_DIR = join(__dirname, '../data');
const BASELINE_FILE = join(DATA_DIR, 'desoto_baseline.json');

/**
 * DeSoto County Incremental Scraper
 * 
 * Strategy:
 * 1. First run: Scrape all inmates, establish baseline
 * 2. Subsequent runs: Only scrape NEW bookings
 * 3. Fast roster check, selective detail scraping
 */

export async function runDesotoIncremental() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting DeSoto County Incremental Scraper');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    // Ensure data directory exists
    if (!existsSync(DATA_DIR)) {
      mkdirSync(DATA_DIR, { recursive: true });
    }

    browser = await newBrowser();
    const page = await newPage(browser);

    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);

    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected');
    }

    // Extract all booking info from roster (fast, no detail clicks)
    const rosterData = await parseRosterWithBookingNumbers(page);
    console.log(`📋 Found ${rosterData.length} inmates on roster`);

    if (rosterData.length === 0) {
      await logIngestion('DESOTO', true, 0, startTime);
      return { success: true, count: 0 };
    }

    // Load baseline (previous roster)
    const baseline = loadBaseline();
    const baselineBookingNumbers = new Set(baseline.map(item => item.bookingNumber));

    // Find NEW bookings
    const newBookings = rosterData.filter(item => !baselineBookingNumbers.has(item.bookingNumber));
    
    // On first run (no baseline), limit to 5 for testing, otherwise process all new
    const isFirstRun = baseline.length === 0;
    const bookingsToProcess = isFirstRun ? newBookings.slice(0, 5) : newBookings;
    
    console.log(`🆕 New bookings found: ${newBookings.length}`);
    console.log(`📊 Baseline size: ${baseline.length}`);
    
    if (isFirstRun) {
      console.log(`⚡ First run detected - limiting to ${bookingsToProcess.length} for testing`);
    }
    
    if (bookingsToProcess.length === 0) {
      console.log('✅ No new bookings to process');
      await logIngestion('DESOTO', true, 0, startTime);
      return { success: true, count: 0 };
    }

    // Only scrape details for NEW bookings
    const records = [];
    for (let i = 0; i < bookingsToProcess.length; i++) {
      const booking = bookingsToProcess[i];
      console.log(`🔍 [${i + 1}/${bookingsToProcess.length}] NEW: ${booking.name} (${booking.bookingNumber})`);

      try {
        await randomDelay(1000, 400);
        await navigateWithRetry(page, booking.detailUrl);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'DESOTO', booking.detailUrl);

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

    // Update baseline with current roster
    saveBaseline(rosterData);
    console.log(`💾 Updated baseline with ${rosterData.length} bookings`);

    await logIngestion('DESOTO', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { 
      success: true, 
      count: records.length, 
      newBookingsFound: newBookings.length,
      newBookingsProcessed: bookingsToProcess.length 
    };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('DESOTO', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Parse roster page and extract booking numbers + detail URLs
 * This is fast because we don't click through to detail pages
 */
async function parseRosterWithBookingNumbers(page) {
  try {
    await page.waitForSelector('table#gvInmates_DXMainTable, a', { timeout: 10000 });
    
    const rosterData = await page.$$eval('a[href*="inmate-details"]', elements =>
      elements.map(el => {
        // Try to extract booking number from link text or nearby elements
        const text = el.textContent.trim();
        const href = el.href;
        
        // Extract booking number from URL if possible
        const match = href.match(/id=([^&]+)/);
        const bookingNumber = match ? match[1] : text;
        
        return {
          bookingNumber: bookingNumber,
          name: text || 'Unknown',
          detailUrl: href
        };
      }).filter(item => item.bookingNumber && item.detailUrl)
    );

    // Remove duplicates by booking number
    const uniqueData = Array.from(
      new Map(rosterData.map(item => [item.bookingNumber, item])).values()
    );

    console.log(`   Extracted ${uniqueData.length} unique booking numbers from roster`);
    return uniqueData;
    
  } catch (error) {
    console.error('⚠️  Error parsing roster:', error.message);
    return [];
  }
}

/**
 * Extract detail pairs from inmate detail page
 */
async function extractDetailPairs(page) {
  try {
    await page.waitForSelector('table, .detainee-detail', { timeout: 5000 });
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

/**
 * Load baseline from file
 */
function loadBaseline() {
  try {
    if (existsSync(BASELINE_FILE)) {
      const data = JSON.parse(readFileSync(BASELINE_FILE, 'utf8'));
      console.log(`📂 Loaded baseline: ${data.length} bookings`);
      return data;
    }
  } catch (error) {
    console.warn('⚠️  Could not load baseline:', error.message);
  }
  console.log('📂 No baseline found, will establish new baseline');
  return [];
}

/**
 * Save current roster as baseline
 */
function saveBaseline(rosterData) {
  try {
    writeFileSync(BASELINE_FILE, JSON.stringify(rosterData, null, 2), 'utf8');
  } catch (error) {
    console.error('⚠️  Could not save baseline:', error.message);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runDesotoIncremental().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runDesotoIncremental;
