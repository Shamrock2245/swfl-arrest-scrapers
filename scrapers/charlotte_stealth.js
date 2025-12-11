// scrapers/charlotte_stealth.js
// Charlotte County scraper with Puppeteer stealth mode and 34-column schema output

import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha, isCloudflareBlocked, waitForCloudflare, humanScroll } from '../shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).charlotte;

const LIST_URL = 'https://inmates.charlottecountyfl.revize.com/bookings';
const BASE_URL = 'https://inmates.charlottecountyfl.revize.com';

/**
 * Main Charlotte County scraper with stealth mode (34-column output)
 */
export async function runCharlotteStealth() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Charlotte County Scraper (Stealth + 34-column)');
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

    // Wait for page to load and check for Cloudflare
    await randomDelay(3000, 1000);

    // Simulate human behavior - scroll the page
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

    // 3) Extract detail URLs from the list page
    const detailUrls = await extractDetailUrls(page);
    console.log(`📋 Found ${detailUrls.length} booking detail URLs`);

    if (detailUrls.length === 0) {
      await browser.close();
      await logIngestion('CHARLOTTE', true, 0, startTime);
      console.log('ℹ️  No bookings found');
      return { success: true, count: 0 };
    }

    // 4) Fetch & parse each detail page
    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Navigating to ${url}`);

      try {
        // Longer random delay to appear more human-like
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
        const record = normalizeRecord34(rawPairs, 'CHARLOTTE', url);

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

    await logIngestion('CHARLOTTE', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    await browser.close();
    return { success: true, count: records.length };
  } catch (error) {
    console.error('❌ Fatal Charlotte error:', error.message);
    if (browser) await browser.close();
    await logIngestion('CHARLOTTE', false, 0, startTime, error.message);
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
 * Charlotte uses Bootstrap forms with label.form-label + input[readonly] pairs
 */
async function extractDetailPairs(page, sourceUrl) {
  const data = {};

  // Extract Bootstrap form-based data (label.form-label + input[readonly])
  const formData = await page.$$eval('.card-body', cards => {
    const result = {};
    cards.forEach(card => {
      // Find all rows with labels and inputs
      const labels = card.querySelectorAll('label.form-label');
      labels.forEach(label => {
        const labelText = label.textContent.trim();
        // Find the next input sibling
        const input = label.parentElement.querySelector('input');
        if (input) {
          const value = input.getAttribute('value') || input.value || '';
          if (labelText && value) {
            result[labelText] = value;
          }
        }
      });
    });
    return result;
  });

  Object.assign(data, formData);

  // Extract the most recent booking info from bookings-table (first tr with data-booking)
  const bookingData = await page.$$eval('#bookings-table tbody tr[data-booking]', rows => {
    if (rows.length === 0) return {};
    // Get the first (most recent) booking
    const firstRow = rows[0];
    const tds = firstRow.querySelectorAll('td');
    // Columns: [button], Book #, Agency, Book Date, Release Date, Rel. Reason
    if (tds.length >= 4) {
      return {
        'Book #': tds[1]?.textContent.trim() || '',
        'Agency': tds[2]?.textContent.trim() || '',
        'Book Date': tds[3]?.textContent.trim() || '',
        'Release Date': tds[4]?.textContent.trim() || '',
        'Rel. Reason': tds[5]?.textContent.trim() || ''
      };
    }
    return {};
  }).catch(() => ({}));

  Object.assign(data, bookingData);

  // Construct Full_Name from First Name and Last Name (Charlotte provides them separately)
  if (data['First Name'] && data['Last Name']) {
    data['Full_Name'] = `${data['Last Name']}, ${data['First Name']}`;
  }

  // Determine Status from Release Date / Release Reason
  if (data['Rel. Reason'] && data['Rel. Reason'] !== 'N/A') {
    data['Status'] = data['Rel. Reason'];
  } else if (data['Release Date'] && data['Release Date'] !== 'N/A') {
    data['Status'] = 'Released';
  } else {
    data['Status'] = 'In Custody';
  }

  // Extract charges from arrest-table (multiple possible)
  const charges = await page.$$eval('.arrest-table tbody tr', rows => {
    const chargeList = [];
    rows.forEach(row => {
      const tds = row.querySelectorAll('td');
      // Columns: Desc., Degree, Agency, Location, Bond Amt.
      if (tds.length >= 5) {
        const desc = tds[0]?.textContent.trim() || '';
        const bondAmt = tds[4]?.textContent.trim() || '0';
        if (desc) {
          chargeList.push({ description: desc, bondAmount: bondAmt });
        }
      }
    });
    return chargeList;
  }).catch(() => []);

  // Combine charges into pipe-separated string
  if (charges.length > 0) {
    data['Charges'] = charges.map(c => c.description).join(' | ');
    // Sum up bond amounts
    const totalBond = charges.reduce((sum, c) => {
      const amt = parseFloat(c.bondAmount.replace(/[^0-9.]/g, '')) || 0;
      return sum + amt;
    }, 0);
    data['Bond_Amount'] = totalBond.toString();
  }

  // Extract mugshot (inline base64 or URL)
  const mugshot = await page.$eval(
    '#inmate-mugshot, img[src*="mug"], img[src*="photo"]',
    (img, baseUrl) => {
      let src = img.getAttribute('src');
      if (!src) return null;
      // If it's a base64 image, return it directly
      if (src.startsWith('data:image')) {
        return src;
      }
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

  console.log('   📋 Extracted fields:', Object.keys(data).join(', '));

  return data;
}

// Allow direct execution via `node scrapers/charlotte_stealth.js`
if (import.meta.url === `file://${process.argv[1]}`) {
  runCharlotteStealth().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runCharlotteStealth;
