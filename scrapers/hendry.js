import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).hendry;

puppeteerExtra.use(StealthPlugin());

const COUNTY_CODE = 'HENDRY';
const BASE_URL = 'https://www.hendrysheriff.org';
const ROSTER_URL = `${BASE_URL}/inmateSearch`;

async function scrapeHendry() {
  console.log(`[${COUNTY_CODE}] Starting scrape...`);
  
  const browser = await puppeteerExtra.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  try {
    const page = await browser.newPage();
    
    // Get roster page
    await page.goto(ROSTER_URL, {
      waitUntil: 'networkidle2',
      timeout: 60000
    });
    
    await page.waitForTimeout(3000);
    
    // Find all inmate detail links
    const inmateLinks = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll('a[href*="inmateSearch/"]'));
      return links
        .map(link => link.href)
        .filter(href => href && /inmateSearch\/\d+/.test(href));
    });
    
    console.log(`[${COUNTY_CODE}] Found ${inmateLinks.length} inmate detail links`);
    
    if (inmateLinks.length === 0) {
      console.log(`[${COUNTY_CODE}] No inmates found`);
      await browser.close();
      return;
    }
    
    const records = [];
    
    // Visit each detail page
    for (const link of inmateLinks) {
      try {
        await page.goto(link, {
          waitUntil: 'networkidle2',
          timeout: 60000
        });
        
        await page.waitForTimeout(2000);
        
        const rawData = await page.evaluate(() => {
          const data = {};
          
          // Extract name - look for h1/h2 that matches name pattern "LAST,FIRST MIDDLE"
          const headings = Array.from(document.querySelectorAll('h1, h2'));
          const nameHeading = headings.find(h => /^[A-Z]+,\s+[A-Z\s]+$/.test(h.textContent.trim()));
          if (nameHeading) {
            data['name'] = nameHeading.textContent.trim();
          }
          
          // Extract all text content
          const bodyText = document.body.textContent;
          
          // Extract Inmate ID - remove the trailing 'M' or other letters
          const inmateIdMatch = bodyText.match(/Inmate ID:\s*([A-Z0-9]+?)(?:[A-Z]ain|\s|$)/);
          if (inmateIdMatch) {
            data['Inmate ID'] = inmateIdMatch[1];
          }
          
          // Extract sex and race
          const genderMatch = bodyText.match(/Gender:\s*([MF])\b/);
          if (genderMatch) data['sex'] = genderMatch[1];
          
          const raceMatch = bodyText.match(/Race:\s*([A-Z])\b/);
          if (raceMatch) data['race'] = raceMatch[1];
          
          // Extract address
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
          
          // Extract physical details for extra_fields
          const heightMatch = bodyText.match(/Height:\s*(\d+\s*ft\s*\d+in)/);
          if (heightMatch) data['height'] = heightMatch[1].trim();
          
          const weightMatch = bodyText.match(/Weight:\s*(\d+)\s*lbs/);
          if (weightMatch) data['weight'] = weightMatch[1];
          
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
              data['total_bond'] = charges.reduce((sum, c) => sum + parseFloat(c.bond.replace(/[^0-9.]/g, '') || 0), 0).toString();
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
        
        // Normalize the record
        const normalized = normalizeRecord(rawData, COUNTY_CODE, rawData.source_url);
        
        // Only add if we have a booking_id (required field)
        if (normalized.booking_id) {
          records.push(normalized);
          console.log(`[${COUNTY_CODE}] Extracted: ${normalized.full_name_last_first} (${normalized.booking_id})`);
        } else {
          console.log(`[${COUNTY_CODE}] Skipping record - no booking_id`);
        }
        
      } catch (error) {
        console.error(`[${COUNTY_CODE}] Error processing ${link}:`, error.message);
      }
    }
    
    console.log(`[${COUNTY_CODE}] Parsed ${records.length} valid records`);
    
    if (records.length > 0) {
      await upsertRecords(config.sheetName, records);
      await mirrorQualifiedToDashboard();
      await logIngestion(COUNTY_CODE, records.length, 0);
    }
    
  } catch (error) {
    console.error(`[${COUNTY_CODE}] Fatal error:`, error);
    await logIngestion(COUNTY_CODE, 0, 1);
  } finally {
    await browser.close();
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  scrapeHendry().catch(console.error);
}

export default scrapeHendry;
