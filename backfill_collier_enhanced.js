// backfill_collier_enhanced.js
// Enhanced backfill for Collier County using date range search

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

const SEARCH_URL = 'https://www2.colliersheriff.org/arrestsearch/Searchmobile.aspx';

/**
 * Format date as MM/DD/YYYY for the form
 */
function formatDate(date) {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const year = date.getFullYear();
  return `${month}/${day}/${year}`;
}

/**
 * Get array of dates for the last N days
 */
function getDateRange(daysBack) {
  const dates = [];
  const today = new Date();
  
  for (let i = 0; i < daysBack; i++) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    dates.push(date);
  }
  
  return dates;
}

/**
 * Search for arrests on a specific booking date
 */
async function searchByDate(page, bookingDate) {
  console.log(`\n📅 Searching for arrests on ${bookingDate}...`);
  
  // Navigate to search form
  await navigateWithRetry(page, SEARCH_URL);
  await randomDelay(1000, 300);
  
  // Fill in the booking date field
  await page.waitForSelector('#txtArrestDt', { timeout: 10000 });
  await page.type('#txtArrestDt', bookingDate);
  await randomDelay(500, 200);
  
  // Click Search button
  await page.click('#btnSearch');
  await randomDelay(3000, 500);
  
  // Wait for results or error message
  await page.waitForTimeout(2000);
  
  // Check if we got results
  const hasResults = await page.evaluate(() => {
    const body = document.body.textContent;
    return !body.includes('No records found') && !body.includes('no results');
  });
  
  if (!hasResults) {
    console.log(`   ℹ️  No arrests found for ${bookingDate}`);
    return [];
  }
  
  // Extract records from results page
  const records = await extractSearchResults(page);
  console.log(`   ✅ Found ${records.length} arrests`);
  
  return records;
}

/**
 * Extract arrest records from search results
 */
async function extractSearchResults(page) {
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

/**
 * Main backfill function
 */
async function backfillCollierEnhanced(daysBack = 10) {
  const startTime = Date.now();
  console.log("═══════════════════════════════════════");
  console.log(`🔄 Starting Collier County Enhanced Backfill (${daysBack} days)`);
  console.log("═══════════════════════════════════════");

  let browser;
  let allRecords = [];

  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // Get date range
    const dates = getDateRange(daysBack);
    console.log(`\n📅 Will search ${dates.length} dates from ${formatDate(dates[dates.length - 1])} to ${formatDate(dates[0])}\n`);

    // Search each date
    for (const date of dates) {
      const dateStr = formatDate(date);
      
      try {
        const records = await searchByDate(page, dateStr);
        
        // Normalize records
        for (const raw of records) {
          try {
            const record = normalizeRecord(raw, "COLLIER", SEARCH_URL);
            if (record?.booking_id) {
              allRecords.push(record);
              console.log(`      ✅ ${record.full_name_last_first || raw.name || "(no name)"}`);
            }
          } catch (e) {
            console.error(`      ⚠️  Normalization failed:`, e?.message || e);
          }
        }
        
        // Small delay between dates to avoid rate limiting
        await randomDelay(2000, 500);
        
      } catch (error) {
        console.error(`   ❌ Error searching ${dateStr}:`, error.message);
        // Continue with next date
      }
    }

    // Upsert to Google Sheets
    console.log(`\n📊 Total records found: ${allRecords.length}`);
    if (allRecords.length > 0) {
      const result = await upsertRecords(config.sheetName, allRecords);
      console.log(
        `✅ Inserted: ${result.inserted}, Updated: ${result.updated}`
      );
      await mirrorQualifiedToDashboard(allRecords);
    }

    await logIngestion("COLLIER_BACKFILL_ENHANCED", true, allRecords.length, startTime);
    console.log("✅ Finished Collier enhanced backfill.");
    console.log("═══════════════════════════════════════\n");
    return { success: true, count: allRecords.length };

  } catch (error) {
    console.error("❌ Fatal error:", error?.message || error);
    if (error?.stack) console.error(error.stack);
    await logIngestion(
      "COLLIER_BACKFILL_ENHANCED",
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

/* ----------------------- CLI support ----------------------- */

const daysBack = parseInt(process.argv[2]) || 10;

backfillCollierEnhanced(daysBack).catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
