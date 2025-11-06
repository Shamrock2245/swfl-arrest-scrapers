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

async function check() {
  const result = await sheets.spreadsheets.values.get({
    spreadsheetId: SHEETS_ID,
    range: 'HENDRY!A1:K12'
  });
  
  console.log('HENDRY sheet data (first 11 columns, 12 rows):');
  result.data.values.forEach((row, i) => {
    console.log(`Row ${i+1}:`, row.slice(0, 7).join(' | '));
  });
}

check();
