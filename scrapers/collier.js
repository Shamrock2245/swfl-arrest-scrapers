// scrapers/collier.js
// Collier County inline data scraper - extracts data directly from Report.aspx

import 'dotenv/config';
import {
  newBrowser,
  newPage,
  navigateWithRetry,
  randomDelay,
  hasCaptcha,
} from "../shared/browser.js";
import { normalizeRecord } from "../normalizers/normalize.js";
import {
  upsertRecords,
  mirrorQualifiedToDashboard,
  logIngestion,
} from "../writers/sheets.js";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, "../config/counties.json"), "utf8")
).collier;

const REPORT_URL = `${config.baseUrl.replace(/\/$/, "")}/arrestsearch/Report.aspx`;

/**
 * Main entry
 */
export async function runCollier() {
  const startTime = Date.now();
  console.log("═══════════════════════════════════════");
  console.log("🚦 Starting Collier County Scraper");
  console.log("═══════════════════════════════════════");

  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    // Navigate to Report.aspx (today's arrests)
    console.log(`📡 Loading: ${REPORT_URL}`);
    await navigateWithRetry(page, REPORT_URL);
    await randomDelay(2000, 500);

    // CAPTCHA check
    if (await hasCaptcha(page))
      throw new Error("CAPTCHA detected - cannot proceed");

    // Extract all arrest records directly from the page
    const records = await extractAllRecords(page);
    console.log(`📊 Extracted ${records.length} raw records`);

    // Normalize records
    const normalized = [];
    for (const raw of records) {
      try {
        const record = normalizeRecord(raw, "COLLIER", REPORT_URL);
        if (record?.booking_id) {
          normalized.push(record);
          console.log(`   ✅ ${record.full_name_last_first || raw.name || "(no name)"}`);
        }
      } catch (e) {
        console.error(`   ⚠️  Normalization failed:`, e?.message || e);
      }
    }

    // Upsert to Google Sheets
    console.log(`\n📊 Parsed ${normalized.length} valid records`);
    if (normalized.length > 0) {
      const result = await upsertRecords(config.sheetName, normalized);
      console.log(
        `✅ Inserted: ${result.inserted}, Updated: ${result.updated}`
      );
      await mirrorQualifiedToDashboard(normalized);
    }

    await logIngestion("COLLIER", true, normalized.length, startTime);
    console.log("✅ Finished Collier successfully.");
    console.log("═══════════════════════════════════════\n");
    return { success: true, count: normalized.length };
  } catch (error) {
    console.error("❌ Fatal error:", error?.message || error);
    if (error?.stack) console.error(error.stack);
    await logIngestion(
      "COLLIER",
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
 * Extract all arrest records from the inline table structure on Report.aspx
 */
async function extractAllRecords(page) {
  await new Promise(r => setTimeout(r, 1000));

  const records = await page.evaluate(() => {
    const results = [];
    const tables = [...document.querySelectorAll('table')];

    // Find tables with the exact pattern: 6 cells with Name, DOB, Residence headers
    const nameTableIndices = [];
    for (let i = 0; i < tables.length; i++) {
      const table = tables[i];
      const cells = [...table.querySelectorAll('td')];
      const cellTexts = cells.map(c => c.textContent.trim());

      // Look for: ["Name", "Date of Birth", "Residence", "LASTNAME,FIRSTNAME", "MM/DD/YYYY", "ADDRESS"]
      if (cellTexts.length === 6 &&
        cellTexts[0] === 'Name' &&
        cellTexts[1] === 'Date of Birth' &&
        cellTexts[2] === 'Residence' &&
        cellTexts[3].includes(',')) {  // Name has comma

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

      // Look ahead in the next 15 tables for related data
      const startIdx = nameData.index + 1;
      const endIdx = Math.min(startIdx + 15, tables.length);

      for (let j = startIdx; j < endIdx; j++) {
        const table = tables[j];
        const cells = [...table.querySelectorAll('td')];
        const cellTexts = cells.map(c => c.textContent.trim());

        // Description table (A#, PIN, Race, Sex, Height, Weight, etc.)
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

        // Charges table - look for "Offense" in the cells
        if (cellTexts.includes('Offense') && cellTexts.includes('Charged')) {
          const offenseIdx = cellTexts.indexOf('Offense');
          const charges = [];

          // Extract offense descriptions (they're usually longer text)
          for (let k = 0; k < cellTexts.length; k++) {
            const text = cellTexts[k];
            // Offense descriptions are typically longer than 15 chars and don't match known labels
            if (text && text.length > 15 &&
              !['Charged', 'Count', 'Offense', 'Hold For', 'Case Number', 'Court Date'].includes(text) &&
              !/^\d{1,2}\/\d{1,2}\/\d{4}$/.test(text)) {  // Not a date
              charges.push(text);
            }
          }

          if (charges.length > 0) {
            record.charges = charges.join(' | ');
          }
        }

        // Bond Status - look for "BONDED" text
        const tableText = table.textContent;
        if (tableText.includes('BONDED')) {
          record.bond_paid = 'BONDED';
        }

        // Stop searching once we have booking number and are past a few tables
        if (record.bookingNumber && j > startIdx + 5) {
          break;
        }
      }

      // Look for mugshot - find all mugshot images and match by index
      const allMugshots = [...document.querySelectorAll('img[src*="PicThumb"]')];
      if (allMugshots.length > results.length) {
        const img = allMugshots[results.length];
        if (img) {
          record.mugshot_url = new URL(img.src, location.href).toString();
        }
      }

      // Only add if we have booking number
      if (record.bookingNumber) {
        results.push(record);
      }
    }

    return results;
  });

  return records;
}

/* ----------------------- direct-run support ----------------------- */

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollier().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

export default runCollier;
