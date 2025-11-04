import puppeteer from 'puppeteer';

async function testTables() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  await page.goto('https://www2.colliersheriff.org/arrestsearch/Report.aspx', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(2000);
  
  const tableData = await page.evaluate(() => {
    const tables = [...document.querySelectorAll('table')];
    const results = [];
    
    for (let i = 0; i < Math.min(50, tables.length); i++) {
      const table = tables[i];
      const cells = [...table.querySelectorAll('td')];
      const cellTexts = cells.map(c => c.textContent.trim());
      
      // Look for tables that might contain charges
      const hasCharged = cellTexts.some(t => t.toLowerCase().includes('charged'));
      const hasOffense = cellTexts.some(t => t.toLowerCase().includes('offense'));
      
      if (hasCharged || hasOffense) {
        results.push({
          index: i,
          cells: cellTexts.slice(0, 20)  // First 20 cells
        });
      }
    }
    
    return results;
  });
  
  console.log(`\nFound ${tableData.length} tables with 'charged' or 'offense':\n`);
  tableData.forEach((data, idx) => {
    console.log(`Table ${idx + 1} (index ${data.index}):`);
    console.log(`  Cells:`, data.cells);
    console.log('');
  });
  
  await browser.close();
}

testTables().catch(console.error);
