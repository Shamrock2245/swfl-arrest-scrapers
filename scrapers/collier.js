import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).collier;

/**
 * Main Collier County scraper
 */
export async function runCollier() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Collier County Scraper');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // Fetch arrest list
    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);

    // Check for CAPTCHA
    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected - cannot proceed');
    }

    // Parse list page to get detail URLs
    const detailUrls = await parseListPage(page);
    console.log(`📋 Found ${detailUrls.length} arrest records`);

    if (detailUrls.length === 0) {
      console.log('ℹ️  No arrests found');
      await logIngestion('COLLIER', true, 0, startTime);
      return { success: true, count: 0 };
    }

    // Fetch details for each arrest
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Fetching: ${url}`);

      try {
        await randomDelay(1000, 400);
        await navigateWithRetry(page, url);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'COLLIER', url);
        
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

      // Mirror qualified to dashboard
      await mirrorQualifiedToDashboard(records);
    }

    await logIngestion('COLLIER', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('COLLIER', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Parse the list page to extract detail URLs
 */
async function parseListPage(page) {
  try {
    // Wait for content to load
    await page.waitForSelector('table, .arrest-list, a[href*="Detail"]', { timeout: 10000 });

    // Extract detail links
    const links = await page.$$eval('a[href*="Detail"]', elements => 
      elements.map(el => el.href).filter(Boolean)
    );

    // Make URLs absolute and dedupe
    const baseUrl = config.baseUrl;
    const uniqueUrls = [...new Set(links.map(url => {
      if (url.startsWith('http')) return url;
      return baseUrl + (url.startsWith('/') ? url : '/' + url);
    }))];

    return uniqueUrls;
  } catch (error) {
    console.error('⚠️  Error parsing list page:', error.message);
    return [];
  }
}

/**
 * Extract key-value pairs from detail page
 */
async function extractDetailPairs(page) {
  try {
    await page.waitForSelector('table, .detail-info', { timeout: 5000 });

    const pairs = await page.evaluate(() => {
      const data = {};

      // Strategy 1: Extract from table rows (label: value)
      document.querySelectorAll('table tr').forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 2) {
          const label = cells[0].textContent.trim();
          const value = cells[1].textContent.trim();
          if (label && value) {
            data[label] = value;
          }
        }
      });

      // Strategy 2: Extract from definition lists
      document.querySelectorAll('dl').forEach(dl => {
        const dts = dl.querySelectorAll('dt');
        const dds = dl.querySelectorAll('dd');
        dts.forEach((dt, idx) => {
          if (dds[idx]) {
            const label = dt.textContent.trim();
            const value = dds[idx].textContent.trim();
            if (label && value) {
              data[label] = value;
            }
          }
        });
      });

      // Strategy 3: Look for labeled divs/spans
      document.querySelectorAll('.field, .data-field, [class*="field"]').forEach(field => {
        const labelEl = field.querySelector('.label, .field-label, label');
        const valueEl = field.querySelector('.value, .field-value, .data');
        
        if (labelEl && valueEl) {
          const label = labelEl.textContent.trim();
          const value = valueEl.textContent.trim();
          if (label && value) {
            data[label] = value;
          }
        }
      });

      // Extract mugshot
      const mugshotImg = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[alt*="photo"]');
      if (mugshotImg) {
        data['mugshot'] = mugshotImg.src;
      }

      // Extract all text content as fallback for charges
      const bodyText = document.body.innerText;
      const chargesMatch = bodyText.match(/Charges?[:\s]+([^\n]+(?:\n[^\n]+)*)/i);
      if (chargesMatch && !data['Charges']) {
        data['Charges'] = chargesMatch[1].trim();
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
  runCollier().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runCollier;
