import 'dotenv/config';
import { newBrowser, newPage, navigateWithRetry, randomDelay, hasCaptcha } from '../shared/browser.js';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).desoto;

export async function runDesoto() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting DeSoto County Scraper');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    console.log(`📡 Loading: ${config.searchUrl}`);
    await navigateWithRetry(page, config.searchUrl);

    if (await hasCaptcha(page)) {
      throw new Error('CAPTCHA detected');
    }

    const detailUrls = await parseRoster(page);
    console.log(`📋 Found ${detailUrls.length} detainees`);

    if (detailUrls.length === 0) {
      await logIngestion('DESOTO', true, 0, startTime);
      return { success: true, count: 0 };
    }

    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Fetching: ${url}`);

      try {
        await randomDelay(1000, 400);
        await navigateWithRetry(page, url);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'DESOTO', url);

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

    await logIngestion('DESOTO', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('DESOTO', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

async function parseRoster(page) {
  try {
    await page.waitForSelector('table#gvInmates_DXMainTable, a', { timeout: 10000 });
    const links = await page.$$eval('a[href*="inmate-details"]', elements =>
      elements.map(el => el.href).filter(Boolean)
    );
    const uniqueUrls = [...new Set(links)];
    console.log(`   Found ${uniqueUrls.length} inmate detail links`);
    return uniqueUrls;
  } catch (error) {
    console.error('⚠️  Error parsing roster:', error.message);
    return [];
  }
}

async function extractDetailPairs(page) {
  try {
    await page.waitForSelector('#tblDetails, table', { timeout: 5000 });
    
    return await page.evaluate(() => {
      const data = {};
      
      // Extract name from header
      const nameHeader = document.querySelector('#HeaderText, h3.header-text span');
      if (nameHeader) {
        data['Full Name'] = nameHeader.textContent.trim();
      }
      
      // Extract personal info from the detail table
      const detailTable = document.querySelector('#tblDetails');
      if (detailTable) {
        const rows = detailTable.querySelectorAll('tr');
        rows.forEach(row => {
          const cells = row.querySelectorAll('td');
          if (cells.length === 2) {
            const label = cells[0].textContent.trim();
            const value = cells[1].textContent.trim();
            // Skip UI text and empty values
            if (label && value && 
                label !== 'Drag a column header here to group by that column' &&
                !label.includes('Change Offset')) {
              data[label] = value;
            }
          }
        });
      }
      
      // Extract charges from the ChargeGrid table
      const chargeRows = document.querySelectorAll('[id*="ChargeGrid_DXDataRow"]');
      const charges = [];
      
      chargeRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
          const chargeText = cells[0]?.textContent?.trim();
          const offenseDate = cells[1]?.textContent?.trim();
          const bond = cells[5]?.textContent?.trim();
          const bondType = cells[6]?.textContent?.trim();
          
          if (chargeText && chargeText !== 'Drag a column header here to group by that column') {
            charges.push({
              charge: chargeText,
              offense_date: offenseDate,
              bond: bond,
              bond_type: bondType
            });
          }
        }
      });
      
      if (charges.length > 0) {
        data['Charges'] = charges.map(c => c.charge).join(' | ');
        data['Bond Amount'] = charges[0].bond;
        data['Bond Type'] = charges[0].bond_type;
        data['Offense Date'] = charges[0].offense_date;
      }
      
      // Extract mugshot
      const mugshot = document.querySelector('img[src*="photo"], img[src*="mugshot"], img[id*="img"]');
      if (mugshot && mugshot.src && !mugshot.src.includes('data:image')) {
        data['Mugshot'] = mugshot.src;
      }
      
      data['source_url'] = window.location.href;
      
      // Extract booking ID from URL parameter
      const urlParams = new URLSearchParams(window.location.search);
      const bidParam = urlParams.get('bid');
      if (bidParam) {
        data['Booking Number'] = decodeURIComponent(bidParam);
      }
      
      return data;
    });
  } catch (error) {
    console.error('⚠️  Error extracting:', error.message);
    return { source_url: page.url() };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runDesoto().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runDesoto;
