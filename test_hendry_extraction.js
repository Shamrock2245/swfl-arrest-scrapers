import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';

puppeteerExtra.use(StealthPlugin());

async function test() {
  const browser = await puppeteerExtra.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Go to a specific inmate detail page
  await page.goto('https://www.hendrysheriff.org/inmateSearch/42729304', {
    waitUntil: 'networkidle2',
    timeout: 60000
  });
  
  await page.waitForTimeout(3000);
  
  const rawData = await page.evaluate(() => {
    const data = {};
    
    // Extract name from h1 or h2
    const nameEl = document.querySelector('h1, h2');
    if (nameEl) {
      data['name'] = nameEl.textContent.trim();
    }
    
    // Extract all text content
    const bodyText = document.body.textContent;
    
    // Extract Inmate ID
    const inmateIdMatch = bodyText.match(/Inmate ID:\s*([A-Z0-9]+)/);
    if (inmateIdMatch) data['Inmate ID'] = inmateIdMatch[1];
    
    // Extract address
    const addressMatch = bodyText.match(/Main Address:\s*([^\n]+)\s*([^\n]+)/);
    if (addressMatch) {
      data['address'] = `${addressMatch[1].trim()} ${addressMatch[2].trim()}`;
    }
    
    // Extract booking date
    const bookedDateMatch = bodyText.match(/Booked Date:\s*([^\n]+)/);
    if (bookedDateMatch) data['booking_date'] = bookedDateMatch[1].trim();
    
    data['source_url'] = window.location.href;
    
    return data;
  });
  
  console.log('Raw extracted data:');
  console.log(JSON.stringify(rawData, null, 2));
  
  await browser.close();
}

test().catch(console.error);
