import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { normalizeRecord } from './normalizers/normalize.js';

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
    
    // Extract name - look for h1/h2 that matches name pattern
    const headings = Array.from(document.querySelectorAll('h1, h2'));
    const nameHeading = headings.find(h => /^[A-Z]+,\s+[A-Z\s]+$/.test(h.textContent.trim()));
    if (nameHeading) {
      data['name'] = nameHeading.textContent.trim();
    }
    
    // Extract all text content
    const bodyText = document.body.textContent;
    
    // Extract Inmate ID - more precise pattern
    const inmateIdMatch = bodyText.match(/Inmate ID:\s*([A-Z0-9]+)/);
    if (inmateIdMatch) data['Inmate ID'] = inmateIdMatch[1];
    
    // Also try to extract sex and race
    const sexMatch = bodyText.match(/Gender:\s*([MF])/);
    if (sexMatch) data['sex'] = sexMatch[1];
    
    const raceMatch2 = bodyText.match(/Race:\s*([A-Z])/);
    if (raceMatch2) data['race'] = raceMatch2[1];
    
    // Extract address - look for the pattern more carefully
    const addressLines = bodyText.match(/Main Address:\s*([^\n]+?)\s*(?:LABELLE|CLEWISTON|MOORE HAVEN)/i);
    if (addressLines) {
      data['address'] = addressLines[1].trim();
    }
    
    // Extract city, state, zip
    const cityStateZip = bodyText.match(/(LABELLE|CLEWISTON|MOORE HAVEN),\s*FL\s*(\d{5})/i);
    if (cityStateZip) {
      data['city'] = cityStateZip[1];
      data['state'] = 'FL';
      data['zipcode'] = cityStateZip[2];
    }
    
    // Extract physical details
    const heightMatch = bodyText.match(/Height:\s*(\d+\s*ft\s*\d+in)/);
    if (heightMatch) data['height'] = heightMatch[1].trim();
    
    const weightMatch = bodyText.match(/Weight:\s*(\d+)\s*lbs/);
    if (weightMatch) data['weight'] = weightMatch[1];
    
    const genderMatch = bodyText.match(/Gender:\s*([MF])\b/);
    if (genderMatch) data['sex'] = genderMatch[1];
    
    const raceMatch = bodyText.match(/Race:\s*([A-Z])\b/);
    if (raceMatch) data['race'] = raceMatch[1];
    
    const ageMatch = bodyText.match(/Age:\s*(\d+)/);
    if (ageMatch) data['age'] = ageMatch[1];
    
    // Extract booking date
    const bookedDateMatch = bodyText.match(/Booked Date:\s*([^\n]+)/);
    if (bookedDateMatch) data['booking_date'] = bookedDateMatch[1].trim();
    
    // Extract charges
    const chargesSection = bodyText.match(/Charges:([\s\S]*?)(?=Notify Me|$)/);
    if (chargesSection) {
      const chargesText = chargesSection[1];
      const charges = [];
      
      const chargeMatches = chargesText.matchAll(/Charge Code:\s*([^\n]+)\s*Charge Description:\s*([^\n]+)\s*Bond Amount:\s*\$([^\n]+)/g);
      for (const match of chargeMatches) {
        charges.push({
          code: match[1].trim(),
          description: match[2].trim(),
          bond: match[3].trim()
        });
      }
      
      if (charges.length > 0) {
        data['charges'] = charges.map(c => c.description).join(' | ');
        data['total_bond'] = charges.reduce((sum, c) => sum + parseFloat(c.bond.replace(/[^0-9.]/g, '') || 0), 0);
      }
    }
    
    // Extract mugshot
    const img = document.querySelector('img[alt*=","]');
    if (img && img.src && !img.src.includes('logo')) {
      data['mugshot'] = img.src;
    }
    
    data['source_url'] = window.location.href;
    
    return data;
  });
  
  console.log('\n=== Raw extracted data ===');
  console.log(JSON.stringify(rawData, null, 2));
  
  console.log('\n=== After normalization ===');
  const normalized = normalizeRecord(rawData, 'HENDRY', rawData.source_url);
  console.log(JSON.stringify(normalized, null, 2));
  
  console.log('\n=== Key fields check ===');
  console.log(`booking_id: ${normalized.booking_id || 'MISSING'}`);
  console.log(`full_name_last_first: ${normalized.full_name_last_first || 'MISSING'}`);
  console.log(`booking_date: ${normalized.booking_date || 'MISSING'}`);
  console.log(`charges_raw: ${normalized.charges_raw || 'MISSING'}`);
  
  await browser.close();
}

test().catch(console.error);
