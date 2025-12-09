import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, existsSync } from 'fs';
import { normalizeRecord34 } from '../normalizers/normalize34.js';
import { upsertRecords34, logIngestion } from '../writers/sheets34.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
    readFileSync(join(__dirname, '../config/counties.json'), 'utf8')
).hendry;

export async function runHendryV2() {
    const startTime = Date.now();
    console.log('═══════════════════════════════════════');
    console.log('🐍 Starting Hendry County Scraper (Python/DrissionPage)');
    console.log('═══════════════════════════════════════');

    try {
        const pythonScript = join(__dirname, 'python/hendry_solver.py');
        console.log(`🚀 Spawning Python script: ${pythonScript}`);

        const records = await runPythonScript(pythonScript);
        console.log(`\\n📦 Received ${records.length} raw records from Python`);

        // Normalize
        const normalizedRecords = [];
        for (const raw of records) {
            if (!raw.Detail_URL && !raw.source_url) continue;

            const url = raw.Detail_URL || raw.source_url;
            const norm = normalizeRecord34(raw, 'HENDRY', url);

            if (norm.Booking_Number) {
                normalizedRecords.push(norm);
                console.log(`   ✅ ${norm.Full_Name} (${norm.Booking_Number})`);
            } else {
                console.log('   ⚠️  Skipping record without Booking_Number');
            }
        }

        console.log(`📊 Valid normalized records: ${normalizedRecords.length}`);

        if (normalizedRecords.length > 0) {
            const result = await upsertRecords34(config.sheetName, normalizedRecords);
            console.log(`✅ Inserted: ${result.inserted}, Updated: ${result.updated}`);
        }

        await logIngestion('HENDRY', true, normalizedRecords.length, startTime);

        return { success: true, count: normalizedRecords.length };

    } catch (error) {
        console.error('❌ Hendry V2 Error:', error);
        await logIngestion('HENDRY', false, 0, startTime, error.message);
        throw error;
    }
}

function runPythonScript(scriptPath, args = []) {
    return new Promise((resolve, reject) => {
        // Check for venv python
        const venvPython = join(process.cwd(), '.venv/bin/python');
        const pythonCmd = existsSync(venvPython) ? venvPython : 'python3';

        console.log(`🐍 Using Python executable: ${pythonCmd}`);
        const proc = spawn(pythonCmd, [scriptPath, ...args]);

        let stdoutData = '';
        let stderrData = '';

        proc.stdout.on('data', (data) => {
            stdoutData += data.toString();
        });

        proc.stderr.on('data', (data) => {
            stderrData += data.toString();
            process.stderr.write(`[PYTHON LOG] ${data}`);
        });

        proc.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Python script exited with code ${code}`));
                return;
            }

            try {
                const lastLine = stdoutData.trim().split('\\n').pop();
                const json = JSON.parse(lastLine);
                resolve(json);
            } catch (e) {
                reject(new Error(`Failed to parse Python output: ${e.message}`));
            }
        });
    });
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
    runHendryV2().catch(console.error);
}

export default runHendryV2;
