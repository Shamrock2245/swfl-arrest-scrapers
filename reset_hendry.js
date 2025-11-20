import 'dotenv/config';
import { google } from 'googleapis';
import { readFileSync } from 'fs';
import scrapeHendry from './scrapers/hendry.js';

const SHEET_ID = process.env.GOOGLE_SHEETS_ID;
const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;

async function resetHendry() {
  console.log('🗑️  Clearing Hendry sheet...');
  
  // Initialize Google Sheets client
  const keyFile = JSON.parse(readFileSync(KEY_PATH, 'utf8'));
  const auth = new google.auth.GoogleAuth({
    credentials: keyFile,
    scopes: ['https://www.googleapis.com/auth/spreadsheets']
  });
  
  const authClient = await auth.getClient();
  const sheets = google.sheets({ version: 'v4', auth: authClient });
  
  // Clear all data rows (keep header)
  await sheets.spreadsheets.values.clear({
    spreadsheetId: SHEET_ID,
    range: 'Hendry!A2:AI'
  });
  
  console.log('✅ Cleared Hendry sheet');
  console.log('🔄 Running fresh scrape...');
  
  // Run scraper
  await scrapeHendry();
  
  console.log('✅ Reset complete!');
}

resetHendry().catch(console.error);
