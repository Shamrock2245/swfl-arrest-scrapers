/**
 * SWFL Arrest Scrapers - Main Entry Point
 * 
 * Usage:
 *   node index.js                    # Run all counties
 *   node index.js collier            # Run specific county
 *   node index.js --update-bonds     # Update bond status
 */

import runAll from './jobs/runAll.js';
import updateBondPaid from './jobs/updateBondPaid.js';
import runCollier from './scrapers/collier.js';
import runCharlotte from './scrapers/charlotte.js';
import runSarasota from './scrapers/sarasota.js';
import runHendry from './scrapers/hendry.js';
import runDesoto from './scrapers/desoto.js';
import runManatee from './scrapers/manatee.js';

const SCRAPERS = {
  collier: runCollier,
  charlotte: runCharlotte,
  sarasota: runSarasota,
  hendry: runHendry,
  desoto: runDesoto,
  manatee: runManatee
};

async function main() {
  const args = process.argv.slice(2);
  
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
SWFL Arrest Scrapers

Usage:
  node index.js                 Run all counties (staggered)
  node index.js collier         Run specific county
  node index.js --update-bonds  Update bond status for last 14 days
  node index.js --help          Show this help

Available counties: ${Object.keys(SCRAPERS).join(', ')}
    `);
    return;
  }

  if (args.includes('--update-bonds')) {
    await updateBondPaid();
    return;
  }

  // Check for specific county
  const county = args.find(arg => !arg.startsWith('--'));
  
  if (county) {
    if (SCRAPERS[county]) {
      await SCRAPERS[county]();
    } else {
      console.error(`❌ Unknown county: ${county}`);
      console.log(`Available: ${Object.keys(SCRAPERS).join(', ')}`);
      process.exit(1);
    }
  } else {
    // Run all counties
    const parallel = args.includes('--parallel');
    await runAll({ parallel });
  }
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
