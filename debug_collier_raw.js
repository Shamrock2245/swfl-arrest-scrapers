// debug_collier_raw.js
// Debug script to see raw data extracted from Collier

import {
  newBrowser,
  newPage,
  navigateWithRetry,
  randomDelay,
} from "./shared/browser.js";

const REPORT_URL = `https://www2.colliersheriff.org/arrestsearch/Report.aspx`;

async function debugCollierRaw() {
  console.log('🔍 Debugging Collier raw data extraction...\n');
  
  let browser;
  try {
    browser = await newBrowser();
    const page = await newPage(browser);

    console.log(`📡 Loading: ${REPORT_URL}`);
    await navigateWithRetry(page, REPORT_URL);
    await randomDelay(2000, 500);

    // Extract first record only for debugging
    const records = await page.evaluate(() => {
      const results = [];
      const tables = [...document.querySelectorAll('table')];
      
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
      
      // Process only the first record
      if (nameTableIndices.length > 0) {
        const nameData = nameTableIndices[0];
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
            } else if (label === 'Booking Date' && value) {
              record.bookingDate = value;
            } else if (label === 'Booking Number' && value && value.length > 5) {
              record.bookingNumber = value;
            } else if (label === 'Agency' && value) {
              record.agency = value;
            }
          }
          
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
          
          if (record.bookingNumber && j > startIdx + 5) {
            break;
          }
        }
        
        const allMugshots = [...document.querySelectorAll('img[src*="PicThumb"]')];
        if (allMugshots.length > 0) {
          const img = allMugshots[0];
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

    console.log('📊 Raw extracted record (first one):');
    console.log(JSON.stringify(records[0], null, 2));
    
    console.log('\n✅ Debug complete');

  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

debugCollierRaw()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
