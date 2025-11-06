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
    range: 'hendry-county-arrests!A1:G12'
  });
  
  console.log('Hendry sheet data:');
  console.log(JSON.stringify(result.data.values, null, 2));
}

check();
