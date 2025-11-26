// scrapers/hendry_stealth.js
// Hendry County scraper with Puppeteer stealth mode, "Read More" click-through, and 34-column schema output

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
).hendry;

const BASE_URL = 'https://www.hendrysheriff.org';
const ROSTER_URL = `${BASE_URL}/inmateSearch`;

/**
 * Main Hendry County scraper with stealth mode and "Read More" functionality (34-column output)
 * @param {number} daysBack - Number of days to go back (default: 30 for last month)
 */
export async function runHendrySteal(daysBack = 30) {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Hendry County Scraper (Stealth + Read More + 34-column)');
  console.log('═══════════════════════════════════════');
  console.log(`📅 Scraping last ${daysBack} days of arrests`);

  let browser = null;

  try {
    // 1) Launch stealth browser
    console.log('🔒 Launching stealth browser...');
    browser = await newBrowser();
    const page = await newPage(browser);

    // 2) Navigate to roster page
    console.log(`📡 Navigating to: ${ROSTER_URL}`);
    await navigateWithRetry(page, ROSTER_URL, { timeout: 60000 });
    await randomDelay(2000, 500);

    // 3) Set sorting to "Date (Newest - Oldest)"
    console.log('🔽 Setting sort order to "Date (Newest - Oldest)"...');
    await page.select('select#sort', 'dateDesc');
    await randomDelay(2000, 500);

    // Wait for page to reload with new sorting
    await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {});
    await randomDelay(1500, 300);

    // 4) Extract all inmate detail URLs from the list page
    console.log('📋 Extracting inmate detail URLs...');
    const detailUrls = await extractDetailUrls(page);
    console.log(`📋 Found ${detailUrls.length} inmate detail URLs`);

    if (detailUrls.length === 0) {
      await browser.close();
      await logIngestion('HENDRY', true, 0, startTime);
      console.log('ℹ️  No inmates found');
      return { success: true, count: 0 };
    }

    // 5) Visit each detail page and extract full information
    const records = [];
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - daysBack);

    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Navigating to ${url}`);

      try {
        await randomDelay(800, 600);
        await navigateWithRetry(page, url, { timeout: 30000 });

        // Extract all data from detail page
        const rawData = await extractDetailPageData(page, url);

        // Check if booking date is within the last N days
        if (rawData['Booked Date']) {
          const bookedDate = new Date(rawData['Booked Date']);
          if (bookedDate < cutoffDate) {
            console.log(`   ⏸️  Reached cutoff date (${bookedDate.toLocaleDateString()}), stopping...`);
            break;
          }
        }

        // Normalize to 34-column schema
        const record = normalizeRecord34(rawData, 'HENDRY', url);

        if (record.Booking_Number) {
          records.push(record);
          console.log(`   ✅ ${record.Full_Name} (${record.Booking_Number}) - Bond: ${record.Bond_Amount}`);
        } else {
          console.log('   ⚠️  Missing Booking_Number after normalization, skipping');
        }
      } catch (err) {
        console.error(`   ⚠️  Error processing ${url}: ${err.message}`);
      }
    }

    console.log(`\n📊 Parsed ${records.length} valid records from last ${daysBack} days`);

    // 6) Write to Sheets
    if (records.length > 0) {
      const result = await upsertRecords34(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
    }

    await logIngestion('HENDRY', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    await browser.close();
    return { success: true, count: records.length };
  } catch (error) {
    console.error('❌ Fatal Hendry error:', error.message);
    if (browser) await browser.close();
    await logIngestion('HENDRY', false, 0, startTime, error.message);
    throw error;
  }
}

/**
 * Extract all inmate detail URLs from the roster list page
 */
async function extractDetailUrls(page) {
  const urls = await page.$$eval('a[href*="inmateSearch/"]', (links) => {
    const uniqueUrls = new Set();
    
    links.forEach(link => {
      const href = link.getAttribute('href');
      if (!href) return;
      
      // Match pattern: /inmateSearch/{ID}
      if (/inmateSearch\/\d+/.test(href)) {
        let fullUrl = href;
        if (!href.startsWith('http')) {
          fullUrl = `https
://www.hendrysheriff.org${href}`;
        }
        uniqueUrls.add(fullUrl);
      }
    });

    return Array.from(uniqueUrls);
  });

  return urls;
}

/**
 * Extract all data from an inmate detail page (after "Read More" has been clicked)
 */
async function extractDetailPageData(page, sourceUrl) {
  const data = {};

  // Extract name from h1
  const name = await page.$eval('h1', (h1) => h1.textContent.trim()).catch(() => null);
  if (name) {
    data['name'] = name;
    data['Full_Name'] = name;
  }

  // Extract posted date
  const postedDate = await page.$eval('*:has-text("Posted on")', (el) => {
    const text = el.textContent;
    const match = text.match(/Posted on\s+(.+?)(?:\s|$)/);
    return match ? match[1].trim() : null;
  }).catch(() => null);
  if (postedDate) {
    data['Posted Date'] = postedDate;
  }

  // Extract Record Details section
  const recordDetails = await page.$$eval('*:has-text("Record Details:")', (sections) => {
    const result = {};
    sections.forEach(section => {
      const text = section.textContent;
      
      // Inmate ID
      const inmateIdMatch = text.match(/Inmate ID:\s*([A-Z0-9]+)/);
      if (inmateIdMatch) result['Inmate ID'] = inmateIdMatch[1];
      
      // Main Address
      const addressMatch = text.match(/Main Address:\s*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Height:|$)/s);
      if (addressMatch) {
        result['Main Address'] = addressMatch[1].trim().replace(/\s+/g, ' ');
      }
      
      // Height
      const heightMatch = text.match(/Height:\s*([^\n]+)/);
      if (heightMatch) result['Height'] = heightMatch[1].trim();
      
      // Weight
      const weightMatch = text.match(/Weight:\s*([^\n]+)/);
      if (weightMatch) result['Weight'] = weightMatch[1].trim();
      
      // Gender
      const genderMatch = text.match(/Gender:\s*([MF])/);
      if (genderMatch) result['Gender'] = genderMatch[1];
      
      // Race
      const raceMatch = text.match(/Race:\s*([A-Z])/);
      if (raceMatch) result['Race'] = raceMatch[1];
      
      // Age
      const ageMatch = text.match(/Age:\s*(\d+)/);
      if (ageMatch) result['Age'] = ageMatch[1];
      
      // Eye Color
      const eyeMatch = text.match(/Eye Color:\s*([A-Z]+)/);
      if (eyeMatch) result['Eye Color'] = eyeMatch[1];
      
      // Hair Color
      const hairMatch = text.match(/Hair Color:\s*([A-Z]+)/);
      if (hairMatch) result['Hair Color'] = hairMatch[1];
    });
    return result;
  }).catch(() => ({}));

  Object.assign(data, recordDetails);

  // Extract Custody Details section
  const custodyDetails = await page.$$eval('*:has-text("Custody Details:")', (sections) => {
    const result = {};
    sections.forEach(section => {
      const text = section.textContent;
      
      // Custody Status
      const statusMatch = text.match(/Custody Status:\s*([A-Z]+)/);
      if (statusMatch) result['Custody Status'] = statusMatch[1];
      
      // Booked Date
      const bookedMatch = text.match(/Booked Date:\s*([^\n]+)/);
      if (bookedMatch) result['Booked Date'] = bookedMatch[1].trim();
    });
    return result;
  }).catch(() => ({}));

  Object.assign(data, custodyDetails);

  // Extract ALL Charges
  const charges = await page.$$eval('*:has-text("Charges:")', (sections) => {
    const allCharges = [];
    sections.forEach(section => {
      const text = section.textContent;
      
      // Split by "Charge Code:" to get individual charges
      const chargeBlocks = text.split(/(?=Charge Code:)/g).slice(1); // Skip first empty element
      
      chargeBlocks.forEach(block => {
        const charge = {};
        
        // Charge Code
        const codeMatch = block.match(/Charge Code:\s*([^\n]+)/);
        if (codeMatch) charge.code = codeMatch[1].trim();
        
        // Charge Description
        const descMatch = block.match(/Charge Description:\s*([^\n]+)/);
        if (descMatch) charge.description = descMatch[1].trim();
        
        // Bond Amount
        const bondMatch = block.match(/Bond Amount:\s*\$?([\d.]+)/);
        if (bondMatch) {
          charge.bond = parseFloat(bondMatch[1]);
        } else {
          charge.bond = 0;
        }
        
        if (charge.code || charge.description) {
          allCharges.push(charge);
        }
      });
    });
    return allCharges;
  }).catch(() => []);

  // Store charges data
  data['charges_array'] = charges;
  
  // Calculate total bond
  const totalBond = charges.reduce((sum, charge) => sum + (charge.bond || 0), 0);
  data['Total Bond'] = totalBond;
  data['Bond Amount'] = `$${totalBond.toFixed(2)}`;
  
  // Combine all charge descriptions
  const chargeDescriptions = charges.map(c => c.description).filter(Boolean).join('; ');
  data['Charges'] = chargeDescriptions;
  
  // Store first two charges separately (for Charge_1 and Charge_2 columns)
  if (charges.length > 0) {
    data['Charge_1'] = charges[0].description || '';
    data['Charge_1_Statute'] = charges[0].code || '';
    data['Charge_1_Bond'] = `$${(charges[0].bond || 0).toFixed(2)}`;
  }
  if (charges.length > 1) {
    data['Charge_2'] = charges[1].description || '';
    data['Charge_2_Statute'] = charges[1].code || '';
    data['Charge_2_Bond'] = `$${(charges[1].bond || 0).toFixed(2)}`;
  }

  // Extract mugshot URL
  const mugshotUrl = await page.$eval('img[src*="mug"], img[src*="photo"], img[alt*="mugshot"]', (img) => {
    let src = img.getAttribute('src');
    if (!src) return null;
    if (!src.startsWith('http')) {
      src = `https://www.hendrysheriff.org${src.startsWith('/') ? src : `/${src}`}`;
    }
    return src;
  }).catch(() => null);

  if (mugshotUrl) {
    data['mugshot'] = mugshotUrl;
    data['Mugshot_URL'] = mugshotUrl;
  }

  // Add source URL
  data['source_url'] = sourceUrl;
  data['Detail_URL'] = sourceUrl;
  
  // Add county
  data['County'] = 'HENDRY';

  return data;
}

// Allow direct execution via `node scrapers/hendry_stealth.js [daysBack]`
if (import.meta.url === `file://${process.argv[1]}`) {
  const daysBack = parseInt(process.argv[2]) || 30;
  
  runHendrySteal(daysBack).catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}

export default runHendrySteal;
