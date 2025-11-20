// verify_collier_data.js
// Verify that Collier County data was written to Google Sheets

import { google } from 'googleapis';
import { readFileSync } from 'fs';
import dotenv from 'dotenv';

dotenv.config();

const SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;

async function verifyCollierData() {
  console.log('🔍 Verifying Collier County data in Google Sheets...\n');

  try {
    // Load credentials
    const credentials = JSON.parse(readFileSync(KEY_PATH, 'utf8'));
    
    // Create auth client
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const authClient = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });

    // Read the Collier tab
    console.log('📊 Reading "Collier" tab...');
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId: SHEETS_ID,
      range: 'Collier!A1:Z100', // Read first 100 rows, all columns
    });

    const rows = response.data.values || [];
    
    if (rows.length === 0) {
      console.log('⚠️  No data found in Collier tab');
      return;
    }

    console.log(`\n✅ Found ${rows.length} rows in Collier tab`);
    console.log(`\n📋 Headers (first row):`);
    console.log(rows[0].join(' | '));
    
    console.log(`\n📊 Sample records (first 5 data rows):`);
    for (let i = 1; i < Math.min(6, rows.length); i++) {
      console.log(`\nRecord ${i}:`);
      const record = rows[i];
      const headers = rows[0];
      
      for (let j = 0; j < Math.min(headers.length, record.length); j++) {
        if (record[j]) {
          console.log(`  ${headers[j]}: ${record[j]}`);
        }
      }
    }

    console.log('\n✅ Verification complete!');

  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    throw error;
  }
}

verifyCollierData()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
