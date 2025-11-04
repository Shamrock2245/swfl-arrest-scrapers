import puppeteer from 'puppeteer';

async function testCharges() {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://www2.colliersheriff.org/arrestsearch/Report.aspx', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(2000);
  
  const chargeData = await page.evaluate(() => {
    const tables = [...document.querySelectorAll('table')];
    const results = [];
    
    console.log(`Total tables: ${tables.length}`);
    
    for (let i = 0; i < tables.length; i++) {
      const table = tables[i];
      const cells = [...table.querySelectorAll('td')];
      const cellTexts = cells.map(c => c.textContent.trim());
      
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
        
        results.push({
          tableIndex: i,
          allCells: cellTexts,
          extractedCharges: charges
        });
      }
    }
    
    return results;
  });
  
  console.log(`\nFound ${chargeData.length} charge tables:\n`);
  chargeData.slice(0, 3).forEach((data, idx) => {
    console.log(`Charge table ${idx + 1}:`);
    console.log(`  Table index: ${data.tableIndex}`);
    console.log(`  All cells:`, data.allCells);
    console.log(`  Extracted charges:`, data.extractedCharges);
    console.log('');
  });
  
  await browser.close();
}

testCharges().catch(console.error);
