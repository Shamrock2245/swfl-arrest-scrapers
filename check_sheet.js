import { google } from 'googleapis';
import { readFileSync } from 'fs';

const keyFile = JSON.parse(readFileSync('./creds/service-account-key.json', 'utf8'));
const auth = new google.auth.GoogleAuth({
  credentials: keyFile,
  scopes: ['https://www.googleapis.com/auth/spreadsheets']
});

const sheets = google.sheets({ version: 'v4', auth });
const spreadsheetId = '1jq1-N7sCbwSiYPLAdI2ZnxhLzym1QsOSuHPy-Gw07Qc';

async function checkData() {
  const response = await sheets.spreadsheets.values.get({
    spreadsheetId,
    range: 'collier-county-arrests!A1:G10'
  });
  
  console.log('Data in collier-county-arrests sheet:');
  console.log(JSON.stringify(response.data.values, null, 2));
}

checkData().catch(console.error);
