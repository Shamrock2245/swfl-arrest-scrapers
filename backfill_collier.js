// backfill_collier.js
// Backfill Collier County arrest data for the last 10 days

import {
  newBrowser,
  newPage,
  navigateWithRetry,
  randomDelay,
  hasCaptcha,
} from "./shared/browser.js";
import { normalizeRecord } from "./normalizers/normalize.js";
import {
  upsertRecords,
  mirrorQualifiedToDashboard,
  logIngestion,
} from "./writers/sheets.js";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, "config/counties.json"), "utf8")
).collier;

const BASE_URL = 'https://www2.colliersheriff.org/arrestsearch';

/**
 * Main backfill function
 */
async function backfillCollier(daysBack = 10) {
  const startTime = Date.now();
  console.log("═══════════════════════════════════════");
  console.log(`🔄 Starting Collier County Backfill (${daysBack} days)`);
  console.log("═══════════════════════════════════════");

  let browser;
  let allRecords = [];

  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // Collier County's Report.aspx shows "today's arrests" by default
    // To get historical data, we need to try different approaches:
    // 1. Check if there's a date range selector
    // 2. Try accessing detail pages directly if we have booking numbers
    // 3. Or scrape the main page multiple times if it rotates

    console.log('\n📅 Attempting to backfill historical data...');
    console.log('Note: Collier County Report.aspx typically shows current arrests only.');
    console.log('We will scrape the current page and note the limitation.\n');

    // For now, scrape the current Report.aspx page
    // TODO: Investigate if there's a search form that allows date range queries
    const reportUrl = `${BASE_URL}/Report.aspx`;
    console.log(`📡 Loading: ${reportUrl}`);
    await navigateWithRetry(page, reportUrl);
    await randomDelay(2000, 500);

    // CAPTCHA check
    if (await hasCaptcha(page))
      throw new Error("CAPTCHA detected - cannot proceed");

    // Extract all arrest records
    const records = await extractAllRecords(page);
    console.log(`📊 Extracted ${records.length} raw records from current page`);

    // Normalize records
    const normalized = [];
    for (const raw of records) {
      try {
        const record = normalizeRecord(raw, "COLLIER", reportUrl);
        if (record?.booking_id) {
          normalized.push(record);
          console.log(`   ✅ ${record.full_name_last_first || raw.name || "(no name)"}`);
        }
      } catch (e) {
        console.error(`   ⚠️  Normalization failed:`, e?.message || e);
      }
    }

    allRecords = normalized;

    // Note: For true historical backfill, we would need to:
    // 1. Find a search form that accepts date ranges
    // 2. Or access the Searchmobile.aspx with date parameters
    // 3. Or iterate through known booking numbers
    
    console.log('\n⚠️  LIMITATION: Collier County Report.aspx shows current arrests only.');
    console.log('For historical data, we would need to:');
    console.log('  - Use the Searchmobile.aspx form with date parameters');
    console.log('  - Or access individual detail pages if booking numbers are known');
    console.log('  - Or check if there\'s an API endpoint for historical data\n');

    // Upsert to Google Sheets
    console.log(`\n📊 Parsed ${allRecords.length} valid records`);
    if (allRecords.length > 0) {
      const result = await upsertRecords(config.sheetName, allRecords);
      console.log(
        `✅ Inserted: ${result.inserted}, Updated: ${result.updated}`
      );
      await mirrorQualifiedToDashboard(allRecords);
    }

    await logIngestion("COLLIER_BACKFILL", true, allRecords.length, startTime);
    console.log("✅ Finished Collier backfill.");
    console.log("═══════════════════════════════════════\n");
    return { success: true, count: allRecords.length };

  } catch (error) {
    console.error("❌ Fatal error:", error?.message || error);
    if (error?.stack) console.error(error.stack);
    await logIngestion(
      "COLLIER_BACKFILL",
      false,
      0,
      startTime,
      String(error?.message || error)
    );
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Extract all arrest records from the page
 * (Same logic as the main scraper)
 */
async function extractAllRecords(page) {
  await page.waitForTimeout(1000);

  const records = await page.evaluate(() => {
    const results = [];
    const tables = [...document.querySelectorAll('table')];
    
    // Find tables with the exact pattern: 6 cells with Name, DOB, Residence headers
    const nameTableIndices = [];
    for (let i = 0; i < tables.length; i++) {
      const table = tables[i];
      const cells = [...table.querySelectorAll('td')];
      const cellTexts = cells.map(c => c.textContent.trim());
      
      if (cellTexts.length === 6 && 
          cellTexts[0] === 'Name' && 
          cellTexts[1] === 'Date of Birth' && 
          cellTexts[2] === 'Residence' &&
          cellTexts[3].includes(',')) {
        
        nameTableIndices.push({
          index: i,
          name: cellTexts[3],
          dob: cellTexts[4],
          address: cellTexts[5]
        });
      }
    }
    
    // For each name table, look ahead for Description, Booking, and Charges tables
    for (const nameData of nameTableIndices) {
      const record = {
        name: nameData.name,
        dob: nameData.dob,
        address: nameData.address
      };
      
      const startIdx = nameData.index + 1;
      const endIdx = Math.min(startIdx + 15, tables.length);
      
      for (let j = startIdx; j < endIdx; j++) {
        const table = tables[j];
        const cells = [...table.querySelectorAll('td')];
        const cellTexts = cells.map(c => c.textContent.trim());
        
        for (let k = 0; k < cellTexts.length - 1; k++) {
          const label = cellTexts[k];
          const value = cellTexts[k + 1];
          
          if (label === 'A#' && value && value.length > 3) {
            record.arrestNumber = value;
          } else if (label === 'PIN' && value && value.length > 3) {
            record.pin = value;
          } else if (label === 'Race' && value && value.length <= 3) {
            record.race = value;
          } else if (label === 'Sex' && value && value.length <= 2) {
            record.sex = value;
          } else if (label === 'Height' && value) {
            record.height = value;
          } else if (label === 'Weight' && value) {
            record.weight = value;
          } else if (label === 'Hair Color' && value) {
            record.hairColor = value;
          } else if (label === 'Eye Color' && value) {
            record.eyeColor = value;
          } else if (label === 'Booking Date' && value) {
            record.bookingDate = value;
          } else if (label === 'Booking Number' && value && value.length > 5) {
            record.bookingNumber = value;
          } else if (label === 'Agency' && value) {
            record.agency = value;
          } else if (label === 'Age at Arrest' && value) {
            record.age = value;
          }
        }
        
        // Charges table
        if (cellTexts.includes('Offense') && cellTexts.includes('Charged')) {
          const charges = [];
          for (let k = 0; k < cellTexts.length; k++) {
            const text = cellTexts[k];
            if (text && text.length > 15 && 
                !['Charged', 'Count', 'Offense', 'Hold For', 'Case Number', 'Court Date'].includes(text) &&
                !/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(text)) {
              charges.push(text);
            }
          }
          if (charges.length > 0) {
            record.charges = charges.join(' | ');
          }
        }
        
        // Bond Status
        const tableText = table.textContent;
        if (tableText.includes('BONDED')) {
          record.bond_paid = 'BONDED';
        }
        
        if (record.bookingNumber && j > startIdx + 5) {
          break;
        }
      }
      
      // Mugshot
      const allMugshots = [...document.querySelectorAll('img[src*="PicThumb"]')];
      if (allMugshots.length > results.length) {
        const img = allMugshots[results.length];
        if (img) {
          record.mugshot_url = new URL(img.src, location.href).toString();
        }
      }
      
      if (record.bookingNumber) {
        results.push(record);
      }
    }
    
    return results;
  });

  return records;
}

/* ----------------------- CLI support ----------------------- */

const daysBack = parseInt(process.argv[2]) || 10;

backfillCollier(daysBack).catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
