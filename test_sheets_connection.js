// test_sheets_connection.js
// Quick test to verify Google Sheets API connection

import { google } from 'googleapis';
import { readFileSync } from 'fs';
import dotenv from 'dotenv';

dotenv.config();

const SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;

async function testConnection() {
  console.log('🔍 Testing Google Sheets Connection...\n');
  console.log(`📋 Sheet ID: ${SHEETS_ID}`);
  console.log(`🔑 Key Path: ${KEY_PATH}\n`);

  try {
    // Load service account credentials
    const credentials = JSON.parse(readFileSync(KEY_PATH, 'utf8'));
    console.log(`✅ Service Account: ${credentials.client_email}`);

    // Create auth client
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const authClient = await auth.getClient();
    const sheets = google.sheets({ version: 'v4', auth: authClient });

    // Try to get spreadsheet metadata
    console.log('\n📡 Fetching spreadsheet metadata...');
    const response = await sheets.spreadsheets.get({
      spreadsheetId: SHEETS_ID,
    });

    console.log(`\n✅ SUCCESS! Connected to spreadsheet:`);
    console.log(`   Title: ${response.data.properties.title}`);
    console.log(`   Locale: ${response.data.properties.locale}`);
    console.log(`   TimeZone: ${response.data.properties.timeZone}`);
    console.log(`\n📊 Available sheets:`);
    
    response.data.sheets.forEach((sheet, idx) => {
      console.log(`   ${idx + 1}. ${sheet.properties.title} (${sheet.properties.gridProperties.rowCount} rows)`);
    });

    console.log('\n✅ Google Sheets connection verified successfully!');
    return true;

  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    if (error.code === 403) {
      console.error('\n⚠️  Permission denied. Make sure the service account has Editor access to the sheet.');
      console.error(`   Share the sheet with: ${JSON.parse(readFileSync(KEY_PATH, 'utf8')).client_email}`);
    }
    throw error;
  }
}

testConnection()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
