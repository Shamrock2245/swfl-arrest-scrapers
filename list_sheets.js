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

async function list() {
  const result = await sheets.spreadsheets.get({
    spreadsheetId: SHEETS_ID
  });
  
  console.log('All sheets:');
  result.data.sheets.forEach(sheet => {
    console.log(`- ${sheet.properties.title} (ID: ${sheet.properties.sheetId})`);
  });
}

list();
