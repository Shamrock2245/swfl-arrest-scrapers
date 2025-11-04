import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha, isCloudflareBlocked } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).charlotte;

/**
 * Main Charlotte County scraper
 */
export async function runCharlotte() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Charlotte County Scraper');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // Navigate to search page
    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);

    // Check for Cloudflare
    if (await isCloudflareBlocked(page)) {
      console.log('⚠️  Cloudflare protection detected - waiting...');
      await page.waitForTimeout(5000); // Wait for Cloudflare challenge
      
      if (await isCloudflareBlocked(page)) {
        throw new Error('Cloudflare blocked - manual intervention required');
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
        await randomDelay(1200, 600); // Slower for Cloudflare
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
