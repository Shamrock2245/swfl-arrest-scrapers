import puppeteer from 'puppeteer';

async function test() {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  await page.goto('https://jail.marionso.com/', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  // Click the Recent button
  await page.click('input[title="Show Recent Bookings"]');
  await page.waitForTimeout(2000);
  
  // Extract table data
  const inmates = await page.evaluate(() => {
    const table = document.querySelector('table');
    if (!table) return [];
    
    const rows = Array.from(table.querySelectorAll('tr')).slice(1); // Skip header
    
    return rows.map(row => {
      const cells = Array.from(row.querySelectorAll('td'));
      if (cells.length < 10) return null;
      
      return {
        booking_number: cells[0]?.textContent.trim(),
        photo_src: cells[1]?.querySelector('img')?.src || '',
        inmate_id: cells[2]?.textContent.trim(),
        last_name: cells[3]?.textContent.trim(),
        first_name: cells[4]?.textContent.trim(),
        middle_name: cells[5]?.textContent.trim(),
        suffix: cells[6]?.textContent.trim(),
        dob: cells[7]?.textContent.trim(),
        sex: cells[8]?.textContent.trim(),
        race: cells[9]?.textContent.trim(),
        booking_date: cells[10]?.textContent.trim(),
        release_date: cells[11]?.textContent.trim(),
        in_custody: cells[12]?.textContent.trim()
      };
    }).filter(Boolean);
  });
  
  console.log(`Found ${inmates.length} inmates`);
  console.log('\nFirst 3 inmates:');
  inmates.slice(0, 3).forEach((inmate, i) => {
    console.log(`\n${i + 1}. ${inmate.last_name}, ${inmate.first_name}`);
    console.log(`   Booking #: ${inmate.booking_number}`);
    console.log(`   Inmate ID: ${inmate.inmate_id}`);
    console.log(`   DOB: ${inmate.dob}`);
    console.log(`   Sex/Race: ${inmate.sex}/${inmate.race}`);
    console.log(`   Booking Date: ${inmate.booking_date}`);
    console.log(`   In Custody: ${inmate.in_custody}`);
  });
  
  await browser.close();
}

test().catch(console.error);
