import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Path to the Python Runner
const PYTHON_SCRIPT = join(__dirname, '../python_scrapers/scrapers/run_sarasota.py');

export async function runSarasota() {
  console.log('═══════════════════════════════════════');
  console.log('🐍 Starting Sarasota County Scraper (Python Bridge)');
  console.log('═══════════════════════════════════════');
  console.log(`🚀 Executing: python3 ${PYTHON_SCRIPT} 1`);

  const child = spawn('python3', [PYTHON_SCRIPT, '1'], {
    stdio: 'inherit' // Pipe output directly to console
  });

  child.on('close', (code) => {
    if (code !== 0) {
      console.error(`❌ Sarasota scraper failed with code ${code}`);
      process.exit(code);
    } else {
      console.log('✅ Sarasota scraper completed successfully.');
    }
  });
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  runSarasota();
}
