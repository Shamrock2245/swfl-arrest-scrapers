// scrapers/hillsborough_stealth.js
// Hillsborough County scraper with Puppeteer stealth mode, form submission, and 34-column schema output

import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';
import { newBrowser, newPage, navigateWithRetry, randomDelay, humanScroll, humanType, humanClick, isCloudflareBlocked, waitForCloudflare } from '../shared/browser.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).hillsborough || { name: 'Hillsborough', sheetName: 'Hillsborough', enabled: true };

const BASE_URL = 'https://webapps.hcso.tampa.fl.us/arrestinquiry';

/**
 * Main Hillsborough County scraper with stealth mode and form submission (34-column output)
 * @param {string} bookingDate - Booking date in MM/DD/YYYY format (default: today)
 */
export async function runHillsboroughSteal(bookingDate = null) {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Hillsborough County Scraper (Stealth + Form + 34-column)');
  console.log('═══════════════════════════════════════');

  // Default to today's date if not provided
  if (!bookingDate) {
    const today = new Date();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const yyyy = today.getFullYear();
    bookingDate = `${mm}/${dd}/${yyyy}`;
  }

  console.log(`📅 Booking Date: ${bookingDate}`);

  let browser = null;

  try {
    // 1) Launch stealth browser
    console.log('🔒 Launching stealth browser...');
    browser = await newBrowser();
    const page = await newPage(browser);

    // 2) Navigate to arrest inquiry form
    console.log(`📡 Navigating to: ${BASE_URL}`);
    await navigateWithRetry(page, BASE_URL, { timeout: 60000 });
    await randomDelay(3000, 1000);
    
    // Simulate human behavior
    await humanScroll(page, 200);
    await randomDelay(1000, 500);
    
    // Check for Cloudflare
    if (await isCloudflareBlocked(page)) {
      console.log('⚠️  Cloudflare detected, waiting for challenge to resolve...');
      await waitForCloudflare(page, 30000);
    }

    // 3) Fill out the form
    console.log('📝 Filling out arrest inquiry form...');

    // Enter booking date with human-like typing
    const dateInput = await page.$('input[placeholder="MM/DD/YYYY"]');
    if (!dateInput) {
      throw new Error('No element found for selector: input[placeholder="MM/DD/YYYY"]');
    }
    await humanType(page, 'input[placeholder="MM/DD/YYYY"]', bookingDate);
    await randomDelay(1000, 500);

    // Check "Include Arrest Details" with human-like click
    const includeDetailsCheckbox = await page.$('input[type="checkbox"]');
    if (includeDetailsCheckbox) {
      const isChecked = await page.$eval('input[type="checkbox"]', el => el.checked);
      if (!isChecked) {
        await humanClick(page, 'input[type="checkbox"]');
        await randomDelay(500, 300);
      }
    }

    // Select "by Booking Date" radio button with human-like click
    const bookingDateRadio = await page.$('input[type="radio"][value="bookingDate"]');
    if (bookingDateRadio) {
      await humanClick(page, 'input[type="radio"][value="bookingDate"]');
      await randomDelay(500, 300);
    }

    console.log('✅ Form filled out');
    await randomDelay(2000, 500);

    // 4) Submit the form (handle reCAPTCHA if present)
    console.log('🔍 Submitting form...');
    
    // Check for reCAPTCHA
    const hasRecaptcha = await page.$('iframe[src*="recaptcha"]').catch(() => null);
    
    if (hasRecaptcha) {
      console.log('⚠️  reCAPTCHA detected - stealth mode may bypass it automatically');
      console.log('⏳ Waiting for reCAPTCHA to resolve...');
      await randomDelay(5000, 2000);
    }

    // Click search button
    const searchButton = await page.$('button[type="submit"], input[type="submit"], button:has-text("Search")');
    if (searchButton) {
      await searchButton.click();
      console.log('🔄 Waiting for results...');
      await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
      await randomDelay(3000, 1000);
    } else {
      console.log('⚠️  Search button not found, trying form submission');
      await page.keyboard.press('Enter');
      await randomDelay(3000, 1000);
    }

    // 5) Check if CAPTCHA blocked us
    const captchaBlocked = await page.$('iframe[src*="recaptcha"]').catch(() => null);
    if (captchaBlocked) {
      console.log('❌ reCAPTCHA blocking - manual intervention required');
      console.log('💡 Suggestion: Run scraper with visible browser to solve CAPTCHA once');
      await browser.close();
      await logIngestion('HILLSBOROUGH', false, 0, startTime, 'reCAPTCHA blocked');
      return { success: false, error: 'reCAPTCHA blocked', count: 0 };
    }

    // 6) Extract arrest records from results page
    console.log('📋 Extracting arrest records...');
    const records = await extractArrestRecords(page);
    console.log(`📊 Found ${records.length} arrest records`);

    if (records.length === 0) {
      await browser.close();
      await logIngestion('HILLSBOROUGH', true, 0, startTime);
      console.log('ℹ️  No arrests found for this date');
      return { success: true, count: 0 };
    }

    // 7) Normalize to 34-column schema
    const normalizedRecords = records.map(raw => normalizeRecord34(raw, 'HILLSBOROUGH', BASE_URL));

    // 8) Write to Sheets
    if (normalizedRecords.length > 0) {
      const result = await upsertRecords34(config.sheetName, normalizedRecords);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
    }

    await logIngestion('HILLSBOROUGH', true, normalizedRecords.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    await browser.close();
    return { success: true, count: normalizedRecords.length };
  } catch (error) {
    console.error('❌ Fatal Hillsborough error:', error.message);
    if (browser) await browser.close();
    await logIngestion('HILLSBOROUGH', false, 0, startTime, error.message);
    throw error;
  }
}

/**
 * Extract arrest records from the results page
 */
async function extractArrestRecords(page) {
  const records = [];

  // Wait for results to load
  await page.waitForSelector('table, .arrest-record, .result-row', { timeout: 10000 }).catch(() => {});

  // Extract data from table or list
  const rawRecords = await page.$$eval('table tr, .arrest-record, .result-row', (rows) => {
    const results = [];

    rows.forEach((row, index) => {
      // Skip header row
      if (index === 0 && row.querySelector('th')) return;

      const record = {};
      const text = row.textContent;

      // Extract booking number
      const bookingMatch = text.match(/Booking\s*#?\s*:?\s*(\d+)/i);
      if (bookingMatch) record['Booking_Number'] = bookingMatch[1];

      // Extract name
      const nameMatch = text.match(/Name\s*:?\s*([A-Z\s,]+)/i);
      if (nameMatch) record['Full_Name'] = nameMatch[1].trim();

      // Extract booking date
      const bookingDateMatch = text.match(/Booking\s*Date\s*:?\s*([\d\/]+)/i);
      if (bookingDateMatch) record['Booking_Date'] = bookingDateMatch[1];

      // Extract release date
      const releaseDateMatch = text.match(/Release\s*Date\s*:?\s*([\d\/]+)/i);
      if (releaseDateMatch) record['Release_Date'] = releaseDateMatch[1];

      // Extract race
      const raceMatch = text.match(/Race\s*:?\s*([A-Z]+)/i);
      if (raceMatch) record['Race'] = raceMatch[1];

      // Extract sex
      const sexMatch = text.match(/Sex\s*:?\s*([MF])/i);
      if (sexMatch) record['Sex'] = sexMatch[1];

      // Extract DOB
      const dobMatch = text.match(/(?:DOB|Date\s*of\s*Birth)\s*:?\s*([\d\/]+)/i);
      if (dobMatch) record['DOB'] = dobMatch[1];

      // Extract charges (if "Include Arrest Details" was checked)
      const chargesMatch = text.match(/Charges?\s*:?\s*([^\n]+)/i);
      if (chargesMatch) record['Charges'] = chargesMatch[1].trim();

      // Extract bond amount
      const bondMatch = text.match(/Bond\s*(?:Amount)?\s*:?\s*\$?([\d,]+(?:\.\d{2})?)/i);
      if (bondMatch) record['Bond_Amount'] = `$${bondMatch[1]}`;

      // Only add if we have at least a booking number or name
      if (record['Booking_Number'] || record['Full_Name']) {
        results.push(record);
      }
    });

    return results;
  }).catch(() => []);

  records.push(...rawRecords);

  // If no records found in table, try alternative extraction
  if (records.length === 0) {
    console.log('⚠️  No records found in table, trying alternative extraction...');
    
    const bodyText = await page.$eval('body', el => el.textContent).catch(() => '');
    
    // Parse body text for arrest records
    const bookingMatches = bodyText.matchAll(/Booking\s*#?\s*:?\s*(\d+)/gi);
    for (const match of bookingMatches) {
      records.push({
        'Booking_Number': match[1],
        'County': 'HILLSBOROUGH'
      });
    }
  }

  return records;
}

// Allow direct execution via `node scrapers/hillsborough_stealth.js [date]`
if (import.meta.url === `file://${process.argv[1]}`) {
  const bookingDate = process.argv[2] || null;  // MM/DD/YYYY format
  
  runHillsboroughSteal(bookingDate).catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runHillsboroughSteal;
