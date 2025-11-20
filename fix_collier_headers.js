// fix_collier_headers.js
// Fix the headers in the Collier sheet to match the schema

import { google } from 'googleapis';
import { readFileSync } from 'fs';
import dotenv from 'dotenv';

dotenv.config();

const SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;

// Expected headers from schema
const CORRECT_HEADERS = [
  "booking_id",
  "full_name_last_first",
  "first_name",
  "last_name",
  "dob",
  "sex",
  "race",
  "arrest_date",
  "arrest_time",
  "booking_date",
  "booking_time",
  "agency",
  "address",
  "city",
  "state",
  "zipcode",
  "charges_raw",
  "charge_1",
  "charge_1_statute",
  "charge_1_bond",
  "charge_2",
  "charge_2_statute",
  "charge_2_bond",
  "total_bond",
  "bond_paid",
  "court_date",
  "case_number",
  "mugshot_url",
  "mugshot_image",
  "source_url",
  "county",
  "ingested_at_iso",
  "qualified_score",
  "is_qualified",
  "extra_fields_json"
];

async function fixCollierHeaders() {
  console.log('🔧 Fixing Collier sheet headers...\n');

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

    // Clear existing data
    console.log('🗑️  Clearing existing Collier data...');
    await sheets.spreadsheets.values.clear({
      spreadsheetId: SHEETS_ID,
      range: 'Collier!A:AJ',
    });

    // Write correct headers
    console.log('📝 Writing correct headers...');
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEETS_ID,
      range: 'Collier!A1',
      valueInputOption: 'USER_ENTERED',
      requestBody: {
        values: [CORRECT_HEADERS]
      }
    });

    console.log('\n✅ Headers fixed! The Collier sheet is now ready.');
    console.log('📋 Headers set:');
    console.log(CORRECT_HEADERS.join(', '));

  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    throw error;
  }
}

fixCollierHeaders()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
