import { exec } from 'child_process';
import util from 'util';
import runDesoto from '../scrapers/desoto.js';
import runLee from '../scrapers/lee_trigger.js'; // GAS Trigger

const execPromise = util.promisify(exec);

// Helper to run Python scripts
async function runPythonScript(scriptPath, countyName) {
  console.log(`🐍 Running ${countyName} (Python)...`);
  try {
    const { stdout, stderr } = await execPromise(`source .venv/bin/activate && python ${scriptPath}`, { shell: '/bin/bash' });
    // console.log(stdout); // Optional: log stdout
    if (stderr) console.error(`[${countyName} Stderr]:`, stderr);

    // Naive count extraction from stdout logs or assume success if no error
    // Our python runners print "Processed X valid records" or similar
    // Let's try to parse it, or just return success
    const countMatch = stdout.match(/Processed (\d+) valid records/);
    const count = countMatch ? parseInt(countMatch[1]) : 0;

    return { success: true, count, note: 'Python Execution Complete' };
  } catch (error) {
    console.error(`❌ ${countyName} Failed:`, error.message);
    return { success: false, count: 0, error: error.message };
  }
}

const COUNTY_RUNNERS = [
  // Python Scrapers (Direct Execution)
  { name: 'Hendry', fn: () => runPythonScript('python_scrapers/scrapers/run_hendry.py', 'Hendry'), offsetMs: 1000 },
  { name: 'Charlotte', fn: () => runPythonScript('python_scrapers/scrapers/run_charlotte.py', 'Charlotte'), offsetMs: 60000 },
  { name: 'Sarasota', fn: () => runPythonScript('python_scrapers/scrapers/run_sarasota.py', 'Sarasota'), offsetMs: 120000 },
  { name: 'Manatee', fn: () => runPythonScript('python_scrapers/scrapers/run_manatee.py', 'Manatee'), offsetMs: 180000 },
  { name: 'Hillsborough', fn: () => runPythonScript('python_scrapers/run_hillsborough.py', 'Hillsborough'), offsetMs: 240000 },
  { name: 'Orange', fn: () => runPythonScript('python_scrapers/run_orange.py', 'Orange'), offsetMs: 300000 },

  // Node.js Scrapers (Imported)
  { name: 'Lee', fn: runLee, offsetMs: 360000 },
  { name: 'DeSoto', fn: runDesoto, offsetMs: 420000 },
];

/**
 * Run all county scrapers (optionally staggered)
 */
export async function runAll(options = {}) {
  const { parallel = false, stopOnError = false } = options;

  console.log('╔═══════════════════════════════════════╗');
  console.log('║   SWFL Arrest Scrapers - Run All     ║');
  console.log('╚═══════════════════════════════════════╝\n');
  console.log(`Mode: ${parallel ? 'Parallel' : 'Staggered Sequential'}\n`);

  const results = [];
  const startTime = Date.now();

  if (parallel) {
    // Run all counties in parallel
    const promises = COUNTY_RUNNERS.map(async (county) => {
      try {
        const result = await county.fn();
        return { county: county.name, ...result };
      } catch (error) {
        console.error(`❌ ${county.name} failed:`, error.message);
        return { county: county.name, success: false, count: 0, error: error.message };
      }
    });

    results.push(...await Promise.all(promises));

  } else {
    // Run sequentially with staggered delays
    for (const county of COUNTY_RUNNERS) {
      if (county.offsetMs > 0) {
        console.log(`⏳ Waiting ${county.offsetMs / 1000}s before ${county.name}...`);
        await sleep(county.offsetMs - (Date.now() - startTime));
      }

      try {
        console.log(`\n🚀 Starting ${county.name} County...`);
        const result = await county.fn();
        results.push({ county: county.name, ...result });
        console.log(`✅ ${county.name} completed\n`);
      } catch (error) {
        console.error(`❌ ${county.name} failed:`, error.message);
        results.push({ county: county.name, success: false, count: 0, error: error.message });

        if (stopOnError) {
          console.error('🛑 Stopping due to error (stopOnError=true)');
          break;
        }
      }
    }
  }

  // Summary
  const totalDuration = Math.round((Date.now() - startTime) / 1000);
  const totalRecords = results.reduce((sum, r) => sum + (r.count || 0), 0);
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;

  console.log('\n╔═══════════════════════════════════════╗');
  console.log('║          Summary Report               ║');
  console.log('╚═══════════════════════════════════════╝');
  console.log(`\n📊 Total Duration: ${totalDuration}s`);
  console.log(`📥 Total Records: ${totalRecords}`);
  console.log(`✅ Successful: ${successful}/${COUNTY_RUNNERS.length}`);
  console.log(`❌ Failed: ${failed}/${COUNTY_RUNNERS.length}\n`);

  results.forEach(r => {
    const icon = r.success ? '✅' : '❌';
    const count = r.count || 0;
    console.log(`  ${icon} ${r.county}: ${count} records`);
  });

  console.log('\n═══════════════════════════════════════\n');

  return {
    success: failed === 0,
    totalRecords,
    results,
    duration: totalDuration
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Allow direct execution
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const parallel = args.includes('--parallel');
  const stopOnError = args.includes('--stop-on-error');

  runAll({ parallel, stopOnError }).catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

export default runAll;
