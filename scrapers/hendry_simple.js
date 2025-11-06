import puppeteerExtra from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

puppeteerExtra.use(StealthPlugin());

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(readFileSync(join(__dirname, '../config/counties.json'), 'utf8')).hendry;

export async function runHendry() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Hendry County Scraper (Simple Mode)');
  console.log('═══════════════════════════════════════');

  let browser;
  try {
    // Simple browser launch (same as test script)
    browser = await puppeteerExtra.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();

    console.log(`📡 Loading: ${config.searchUrl}`);
    await page.goto(config.searchUrl, {
      waitUntil: 'networkidle2',
      timeout: 60000
    });

    // Wait for JavaScript to render
    await page.waitForTimeout(5000);

    const detailUrls = await parseRoster(page);
    console.log(`📋 Found ${detailUrls.length} inmates`);

    if (detailUrls.length === 0) {
      await logIngestion('HENDRY', true, 0, startTime);
      return { success: true, count: 0 };
    }

    const records = [];
    for (let i = 0; i < detailUrls.length; i++) {
      const url = detailUrls[i];
      console.log(`🔍 [${i + 1}/${detailUrls.length}] Fetching: ${url}`);

      try {
        await page.waitForTimeout(2000);
        await page.goto(url, {
          waitUntil: 'networkidle2',
          timeout: 30000
        });
        await page.waitForTimeout(2000);

        const rawPairs = await extractDetailPairs(page);
        const record = normalizeRecord(rawPairs, 'HENDRY', url);
        
        if (record.booking_id) {
          records.push(record);
          console.log(`   ✅ ${record.full_name_last_first} (${record.booking_id})`);
        }
      } catch (error) {
        console.error(`   ⚠️  Error: ${error.message}`);
      }
    }

    console.log(`\n📊 Parsed ${records.length} valid records`);

    if (records.length > 0) {
      const result = await upsertRecords(config.sheetName, records);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
      await mirrorQualifiedToDashboard(records);
    }

    await logIngestion('HENDRY', true, records.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('HENDRY', false, 0, startTime, error.message);
    throw error;
  } finally {
    if (browser) await browser.close();
  }
}

async function parseRoster(page) {
  try {
    const links = await page.evaluate(() => {
      const allLinks = Array.from(document.querySelectorAll('a'));
      const inmateLinks = allLinks.filter(a => {
        const text = a.textContent.trim();
        const isNameFormat = /^[A-Z]+,\s+[A-Z\s]+$/.test(text);
        const hasInmateUrl = a.href && /inmateSearch\/\d+/.test(a.href);
        return isNameFormat && hasInmateUrl;
      });
      
      return inmateLinks.map(a => a.href);
    });
    
    const uniqueUrls = [...new Set(links)];
    console.log(`   Found ${uniqueUrls.length} unique inmate detail URLs`);
    
    return uniqueUrls.slice(0, 50);
  } catch (error) {
    console.error('⚠️  Error parsing roster:', error.message);
    return [];
  }
}

async function extractDetailPairs(page) {
  try {
    return await page.evaluate(() => {
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
      
      // Extract address (multi-line)
      const addressMatch = bodyText.match(/Main Address:\s*([^\n]+)\s*([^\n]+)/);
      if (addressMatch) {
        data['address'] = `${addressMatch[1].trim()} ${addressMatch[2].trim()}`;
      }
      
      // Extract physical details
      const heightMatch = bodyText.match(/Height:\s*([^\n]+)/);
      if (heightMatch) data['height'] = heightMatch[1].trim();
      
      const weightMatch = bodyText.match(/Weight:\s*([^\n]+)/);
      if (weightMatch) data['weight'] = weightMatch[1].trim();
      
      const genderMatch = bodyText.match(/Gender:\s*([MF])/);
      if (genderMatch) data['gender'] = genderMatch[1];
      
      const raceMatch = bodyText.match(/Race:\s*([A-Z])/);
      if (raceMatch) data['race'] = raceMatch[1];
      
      const ageMatch = bodyText.match(/Age:\s*(\d+)/);
      if (ageMatch) data['age'] = ageMatch[1];
      
      const eyeColorMatch = bodyText.match(/Eye Color:\s*([A-Z]+)/);
      if (eyeColorMatch) data['eye_color'] = eyeColorMatch[1];
      
      const hairColorMatch = bodyText.match(/Hair Color:\s*([A-Z]+)/);
      if (hairColorMatch) data['hair_color'] = hairColorMatch[1];
      
      // Extract custody details
      const statusMatch = bodyText.match(/Custody Status:\s*([A-Z]+)/);
      if (statusMatch) data['custody_status'] = statusMatch[1];
      
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
          data['charges_raw'] = JSON.stringify(charges);
        }
      }
      
      // Extract mugshot
      const img = document.querySelector('img[alt*=","], img[src*="photo"], img[src*="mugshot"]');
      if (img && img.src) {
        data['mugshot'] = img.src;
      }
      
      data['source_url'] = window.location.href;
      
      return data;
    });
  } catch (error) {
    console.error('⚠️  Error extracting detail pairs:', error.message);
    return { source_url: page.url() };
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runHendry().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runHendry;
