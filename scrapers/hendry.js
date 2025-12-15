// scrapers/hendry.js
// Hendry County scraper - bridges Python solver to Google Sheets
// Uses DrissionPage Python solver for extraction, Node.js for Sheets writing

import 'dotenv/config';
import { spawn } from 'child_process';
import { normalizeRecord } from '../normalizers/normalize.js';
import { upsertRecords, mirrorQualifiedToDashboard, logIngestion } from '../writers/sheets.js';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).hendry;

/**
 * Run the Python Hendry solver and parse output
 * @param {number} maxPages - Max pages to scrape (default: 10)
 * @param {number} maxRecords - Max records to scrape (default: 100)
 * @returns {Promise<Array>} Array of raw records from Python
 */
async function runPythonSolver(maxPages = 10, maxRecords = 100) {
  return new Promise((resolve, reject) => {
    const pythonPath = 'python3';
    const scriptPath = join(__dirname, 'python', 'hendry_solver.py');

    console.log(`🐍 Running Python Hendry solver...`);
    console.log(`   Max pages: ${maxPages}, Max records: ${maxRecords}`);

    const env = {
      ...process.env,
      HENDRY_MAX_PAGES: String(maxPages),
      HENDRY_MAX_RECORDS: String(maxRecords)
    };

    const python = spawn(pythonPath, [scriptPath], { env });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      // Stream stderr for real-time progress
      process.stderr.write(data.toString());
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python solver exited with code ${code}: ${stderr}`));
        return;
      }

      try {
        // Parse JSON from stdout (last line should be the JSON array)
        const records = JSON.parse(stdout.trim());
        console.log(`✅ Python solver returned ${records.length} records`);
        resolve(records);
      } catch (err) {
        reject(new Error(`Failed to parse Python output: ${err.message}`));
      }
    });

    python.on('error', (err) => {
      reject(new Error(`Failed to spawn Python: ${err.message}`));
    });
  });
}

/**
 * Normalize Python record to match our schema
 */
function normalizeHendryRecord(raw, sourceUrl) {
  // Map Python field names to our normalizer's expected format
  const mapped = {
    'Booking Number': raw.Booking_Number || raw.Booking_ID,
    'Full Name': raw.Full_Name,
    'First Name': raw.First_Name,
    'Last Name': raw.Last_Name,
    'DOB': raw.DOB,
    'Sex': raw.Sex,
    'Race': raw.Race,
    'Booking Date': raw.Booking_Date,
    'Height': raw.Height,
    'Weight': raw.Weight,
    'Address': raw.Address,
    'Charges': raw.Charges,
    'Bond Amount': raw.Bond_Amount,
    'mugshot': raw.Mugshot_URL,
    'source_url': raw.Detail_URL || sourceUrl
  };

  return normalizeRecord(mapped, 'HENDRY', raw.Detail_URL || sourceUrl);
}

/**
 * Main entry point for Hendry scraper
 */
export async function runHendry(maxPages = 10, maxRecords = 100) {
  const startTime = Date.now();
  console.log('═══════════════════════════════════════');
  console.log('🚦 Starting Hendry County Scraper (Python Bridge)');
  console.log('═══════════════════════════════════════');

  try {
    // 1) Run Python solver
    const rawRecords = await runPythonSolver(maxPages, maxRecords);

    if (rawRecords.length === 0) {
      console.log('ℹ️  No inmates found');
      await logIngestion('HENDRY', true, 0, startTime);
      return { success: true, count: 0 };
    }

    // 2) Normalize records
    console.log(`\n📊 Normalizing ${rawRecords.length} records...`);
    const normalized = [];

    for (const raw of rawRecords) {
      try {
        const record = normalizeHendryRecord(raw, 'https://www.hendrysheriff.org/inmateSearch');

        if (record?.booking_id) {
          normalized.push(record);
          console.log(`   ✅ ${record.full_name_last_first || raw.Full_Name}`);
        }
      } catch (err) {
        console.error(`   ⚠️  Normalization failed for ${raw.Full_Name}: ${err.message}`);
      }
    }

    console.log(`\n📊 Parsed ${normalized.length} valid records`);

    // 3) Upsert to Google Sheets
    if (normalized.length > 0) {
      const result = await upsertRecords(config.sheetName, normalized);
      console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
      await mirrorQualifiedToDashboard(normalized);
    }

    await logIngestion('HENDRY', true, normalized.length, startTime);

    const duration = Math.round((Date.now() - startTime) / 1000);
    console.log(`⏱️  Total execution time: ${duration}s`);
    console.log('═══════════════════════════════════════\n');

    return { success: true, count: normalized.length };

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    await logIngestion('HENDRY', false, 0, startTime, error.message);
    throw error;
  }
}

// Direct execution support
if (import.meta.url === `file://${process.argv[1]}`) {
  const maxPages = parseInt(process.argv[2]) || 10;
  const maxRecords = parseInt(process.argv[3]) || 100;

  runHendry(maxPages, maxRecords).catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runHendry;
