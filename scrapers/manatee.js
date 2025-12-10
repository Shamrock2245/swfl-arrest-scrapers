// scrapers/manatee.js
// BRIDGE: Runs Python DrissionPage scraper -> Google Sheets Output

import { exec } from 'child_process';
import { promisify } from 'util';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import 'dotenv/config';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to your Python scraper
const PYTHON_SCRIPT = join(__dirname, '../python_scrapers/scrapers/manatee_solver.py');

export async function runManatee() {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🐍 Starting Manatee County Scraper (Python Bridge)');
  console.log('═══════════════════════════════════════');

  try {
    // 1. Run Python Script
    // Default to 21 days back, 10 pages max (or whatever defaults you prefer)
    // For now we use the "Quick Scrape" defaults we set in Python, or pass args here:
    // python3 manatee_solver.py 21 1
    const command = `python3 "${PYTHON_SCRIPT}" 21 1`;

    console.log(`🚀 Executing: ${command}`);
    const { stdout, stderr } = await execAsync(command, { maxBuffer: 1024 * 1024 * 10 }); // 10MB buffer

    // Print stderr (logs) to console so user sees progress
    console.error(stderr);

    // 2. Parse JSON Output
    let records = [];
    try {
      // Find the last valid JSON array in stdout
      const lines = stdout.trim().split('\n');
      const jsonLine = lines[lines.length - 1]; // usually the last line
      records = JSON.parse(jsonLine);
    } catch (parseErr) {
      console.error('❌ Failed to parse Python output:', parseErr);
      console.log('Raw Stdout:', stdout);
      throw new Error('Python scraper did not return valid JSON');
    }

    console.log(`\n📊 Received ${records.length} records from Python`);

    // 3. Write to Sheets (using existing Node.js pipeline utils)
    if (records.length > 0) {
      // Normalize or Ensure fields fit schema?
      // Python scraper outputs keys like "Full_Name", "Booking_Number", "Bond_Amount"
      // which match the schema keys expected by upsertRecords34 loosely.
      // We might need to map them if they don't match exactly.

      // Check first record keys
      // console.log('Sample Record Keys:', Object.keys(records[0]));

      const result = await upsertRecords34('Manatee', records);
      console.log(`✅ Uploaded to Sheets - Inserted: ${result.inserted}, Updated: ${result.updated}`);
    } else {
      console.log('ℹ️  No records to upload.');
    }

    await logIngestion('MANATEE', true, records.length, startTime);
    return { success: true, count: records.length };

  } catch (error) {
    console.error('❌ Fatal Manatee Bridge error:', error);
    await logIngestion('MANATEE', false, 0, startTime, error.message);
    throw error;
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runManatee();
}
