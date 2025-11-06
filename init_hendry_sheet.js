import { google } from 'googleapis';
import { readFileSync } from 'fs';

const SHEETS_ID = process.env.GOOGLE_SHEETS_ID;
const KEY_PATH = process.env.GOOGLE_SERVICE_ACCOUNT_KEY_PATH;

const keyFile = JSON.parse(readFileSync(KEY_PATH, 'utf8'));
const auth = new google.auth.JWT(
  keyFile.client_email,
  null,
  keyFile.private_key,
  ['https://www.googleapis.com/auth/spreadsheets']
);

const sheets = google.sheets({ version: 'v4', auth });

const SCHEMA_HEADERS = [
  'booking_id', 'full_name_last_first', 'first_name', 'last_name', 'dob', 'sex', 'race',
  'arrest_date', 'arrest_time', 'booking_date', 'booking_time', 'agency', 'address', 'city',
  'state', 'zipcode', 'charges_raw', 'charge_1', 'charge_1_statute', 'charge_1_bond',
  'charge_2', 'charge_2_statute', 'charge_2_bond', 'total_bond', 'bond_paid', 'court_date',
  'case_number', 'mugshot_url', 'mugshot_image', 'source_url', 'county', 'ingested_at_iso',
  'qualified_score', 'is_qualified', 'extra_fields_json'
];

async function init() {
  try {
    // Write headers
    await sheets.spreadsheets.values.update({
      spreadsheetId: SHEETS_ID,
      range: 'hendry-county-arrests!A1:AI1',
      valueInputOption: 'RAW',
      resource: {
        values: [SCHEMA_HEADERS]
      }
    });
    
    console.log('✅ Hendry sheet initialized with headers');
  } catch (error) {
    console.error('Error:', error.message);
  }
}

init();
