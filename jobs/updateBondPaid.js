import { newBrowser, newPage, navigateWithRetry, randomDelay } from '../shared/browser.js';
import { readRecentRecords, upsertRecords } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const counties = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8'));

const COUNTY_SHEETS = [
  'collier-county-arrests',
  'charlotte-county-arrests',
  'sarasota-county-arrests',
  'hendry-county-arrests',
  'desoto-county-arrests',
  'manatee-county-arrests'
];

/**
 * Update bond_paid status for recent arrests (last 14 days)
 */
export async function updateBondPaid(options = {}) {
  const { daysBack = 14 } = options;
  
  console.log('╔═══════════════════════════════════════╗');
  console.log('║    Update Bond Paid Status            ║');
  console.log('╚═══════════════════════════════════════╝\n');
  console.log(`Looking back: ${daysBack} days\n`);

  const startTime = Date.now();
  let browser;

  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    const allResults = [];

    for (const sheetName of COUNTY_SHEETS) {
      console.log(`\n📋 Processing: ${sheetName}`);
      
      try {
        // Read recent records from this sheet
        const records = await readRecentRecords(sheetName, daysBack);
        console.log(`   Found ${records.length} records from last ${daysBack} days`);

        if (records.length === 0) continue;

        let updated = 0;
        let unchanged = 0;
        let failed = 0;

        for (const record of records) {
          const sourceUrl = record.source_url;
          if (!sourceUrl) {
            unchanged++;
            continue;
          }

          try {
            // Re-fetch the detail page
            await randomDelay(1200, 600);
            await navigateWithRetry(page, sourceUrl, { timeout: 15000 });

            // Check bond status on page
            const bondPaidStatus = await extractBondPaidStatus(page);
            
            if (bondPaidStatus && bondPaidStatus !== record.bond_paid) {
              // Status changed - update record
              record.bond_paid = bondPaidStatus;
              record.ingested_at_iso = new Date().toISOString();
              
              await upsertRecords(sheetName, [record]);
              console.log(`   ✅ Updated ${record.booking_id}: bond_paid = ${bondPaidStatus}`);
              updated++;
            } else {
              unchanged++;
            }

          } catch (error) {
            console.error(`   ⚠️  Error checking ${record.booking_id}: ${error.message}`);
            failed++;
          }
        }

        allResults.push({
          sheet: sheetName,
          total: records.length,
          updated,
          unchanged,
          failed
        });

        console.log(`   📊 Updated: ${updated}, Unchanged: ${unchanged}, Failed: ${failed}`);

      } catch (error) {
        console.error(`   ❌ Error processing ${sheetName}: ${error.message}`);
      }
    }

    // Summary
    const totalDuration = Math.round((Date.now() - startTime) / 1000);
    const totalUpdated = allResults.reduce((sum, r) => sum + r.updated, 0);
    const totalRecords = allResults.reduce((sum, r) => sum + r.total, 0);

    console.log('\n╔═══════════════════════════════════════╗');
    console.log('║          Summary Report               ║');
    console.log('╚═══════════════════════════════════════╝');
    console.log(`\n⏱️  Total Duration: ${totalDuration}s`);
    console.log(`📊 Total Records Checked: ${totalRecords}`);
    console.log(`✅ Total Updated: ${totalUpdated}\n`);

    allResults.forEach(r => {
      if (r.total > 0) {
        console.log(`  ${r.sheet}: ${r.updated}/${r.total} updated`);
      }
    });

    console.log('\n═══════════════════════════════════════\n');

    return {
      success: true,
      totalUpdated,
      totalRecords,
      results: allResults,
      duration: totalDuration
    };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

/**
 * Extract bond paid status from detail page
 */
async function extractBondPaidStatus(page) {
  try {
    const status = await page.evaluate(() => {
      const bodyText = document.body.innerText.toLowerCase();
      
      // Look for explicit status indicators
      if (bodyText.includes('bond posted') || 
          bodyText.includes('bond paid') ||
          bodyText.includes('released') ||
          bodyText.includes('bail posted')) {
        return 'TRUE';
      }
      
      if (bodyText.includes('not posted') || 
          bodyText.includes('not paid') ||
          bodyText.includes('unpaid') ||
          bodyText.includes('in custody')) {
        return 'FALSE';
      }

      // Look in table cells
      const cells = Array.from(document.querySelectorAll('td'));
      for (const cell of cells) {
        const text = cell.textContent.toLowerCase().trim();
        if (text.includes('bond') && text.includes('status')) {
          // Next cell might have status
          const nextCell = cell.nextElementSibling;
          if (nextCell) {
            const statusText = nextCell.textContent.toLowerCase().trim();
            if (statusText.includes('posted') || statusText.includes('paid') || statusText.includes('released')) {
              return 'TRUE';
            }
            if (statusText.includes('not') || statusText.includes('unpaid')) {
              return 'FALSE';
            }
          }
        }
      }

      return null;
    });

    return status;
  } catch (error) {
    return null;
  }
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const daysBack = args.includes('--days') ? 
    parseInt(args[args.indexOf('--days') + 1]) : 14;

  updateBondPaid({ daysBack }).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default updateBondPaid;
