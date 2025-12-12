import runCollier from '../scrapers/collier.js';
import runCharlotteV2 from '../scrapers/charlotte_v2.js';
import runSarasotaV2 from '../scrapers/sarasota_v2.js';
import runHendryV2 from '../scrapers/hendry_v2.js';
import runDesoto from '../scrapers/desoto.js';
import { runManatee } from '../scrapers/manatee.js'; // Python Bridge

const COUNTY_RUNNERS = [
  // { name: 'Collier', fn: runCollier, offsetMs: 0 }, // Returning 0 records
  { name: 'Hendry', fn: runHendryV2, offsetMs: 1000 },      // Python V2
  { name: 'Charlotte', fn: runCharlotteV2, offsetMs: 60000 }, // Python V2
  { name: 'Sarasota', fn: runSarasotaV2, offsetMs: 120000 },  // Python V2
  { name: 'Manatee', fn: runManatee, offsetMs: 180000 },     // Python Bridge
  // { name: 'DeSoto', fn: runDesoto, offsetMs: 360000 },      // Slow/Unknown
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
