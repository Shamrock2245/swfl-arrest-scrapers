/**
 * =========================================================
 * COUNTY STATISTICS FUNCTIONS
 * Add this to your Code.gs file in the GAS project
 * =========================================================
 */

/**
 * Get arrest statistics for all active counties for today
 * Called by Form.html to populate the county dashboard
 * @returns {Object} Statistics object keyed by county name
 */
function getCountyStatistics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const counties = ['lee', 'collier', 'charlotte'];
  const stats = {};
  
  counties.forEach(county => {
    try {
      // Try to get the sheet for this county
      const sheetName = county.charAt(0).toUpperCase() + county.slice(1);
      const sheet = ss.getSheetByName(sheetName) || ss.getSheetByName(county);
      
      if (!sheet) {
        stats[county] = getEmptyStats();
        return;
      }
      
      const data = sheet.getDataRange().getValues();
      if (data.length < 2) {
        stats[county] = getEmptyStats();
        return;
      }
      
      const headers = data[0].map(h => String(h).toLowerCase().trim());
      const dateCol = findColumnIndex(headers, ['date', 'arrest_date', 'booking_date', 'arrest date', 'booking date']);
      const genderCol = findColumnIndex(headers, ['gender', 'sex']);
      const bondCol = findColumnIndex(headers, ['bond', 'bond_amount', 'bond amount', 'total_bond', 'total bond']);
      const chargeCol = findColumnIndex(headers, ['charge', 'charges', 'offense', 'crime', 'charge_description']);
      
      // Filter to today's arrests
      const todayArrests = data.slice(1).filter(row => {
        if (dateCol === -1) return true; // If no date column, include all
        const rowDate = new Date(row[dateCol]);
        return rowDate >= today;
      });
      
      // Calculate statistics
      const countyStats = {
        total: todayArrests.length,
        male: 0,
        female: 0,
        avgBond: 0,
        crimes: {}
      };
      
      let totalBond = 0;
      let bondCount = 0;
      
      todayArrests.forEach(row => {
        // Gender count
        if (genderCol !== -1) {
          const gender = String(row[genderCol]).toLowerCase().trim();
          if (gender === 'm' || gender === 'male') {
            countyStats.male++;
          } else if (gender === 'f' || gender === 'female') {
            countyStats.female++;
          }
        }
        
        // Bond amount
        if (bondCol !== -1) {
          const bond = parseFloat(String(row[bondCol]).replace(/[,$]/g, ''));
          if (!isNaN(bond) && bond > 0) {
            totalBond += bond;
            bondCount++;
          }
        }
        
        // Crime type categorization
        if (chargeCol !== -1) {
          const charge = String(row[chargeCol]).toUpperCase();
          const crimeType = categorizeCrime(charge);
          countyStats.crimes[crimeType] = (countyStats.crimes[crimeType] || 0) + 1;
        }
      });
      
      // Calculate average bond
      if (bondCount > 0) {
        countyStats.avgBond = Math.round(totalBond / bondCount);
      }
      
      stats[county] = countyStats;
      
    } catch (error) {
      console.error(`Error processing ${county}:`, error);
      stats[county] = getEmptyStats();
    }
  });
  
  return stats;
}

/**
 * Find column index by checking multiple possible header names
 * @param {Array} headers - Array of header names (lowercase)
 * @param {Array} possibleNames - Array of possible column names to match
 * @returns {number} Column index or -1 if not found
 */
function findColumnIndex(headers, possibleNames) {
  for (let i = 0; i < headers.length; i++) {
    for (const name of possibleNames) {
      if (headers[i].includes(name.toLowerCase())) {
        return i;
      }
    }
  }
  return -1;
}

/**
 * Categorize a charge description into a crime type
 * @param {string} charge - The charge description
 * @returns {string} Crime category
 */
function categorizeCrime(charge) {
  const chargeUpper = charge.toUpperCase();
  
  if (chargeUpper.includes('DUI') || chargeUpper.includes('DWI') || chargeUpper.includes('ALCOHOL')) {
    return 'DUI';
  }
  if (chargeUpper.includes('BATTERY') || chargeUpper.includes('ASSAULT') || chargeUpper.includes('DOMESTIC')) {
    return 'Battery';
  }
  if (chargeUpper.includes('THEFT') || chargeUpper.includes('BURGLARY') || chargeUpper.includes('ROBBERY') || chargeUpper.includes('LARCENY')) {
    return 'Theft';
  }
  if (chargeUpper.includes('DRUG') || chargeUpper.includes('COCAINE') || chargeUpper.includes('CANNABIS') || 
      chargeUpper.includes('MARIJUANA') || chargeUpper.includes('CONTROLLED') || chargeUpper.includes('POSSESSION')) {
    return 'Drug';
  }
  if (chargeUpper.includes('FRAUD') || chargeUpper.includes('FORGERY') || chargeUpper.includes('IDENTITY')) {
    return 'Fraud';
  }
  if (chargeUpper.includes('TRAFFIC') || chargeUpper.includes('LICENSE') || chargeUpper.includes('DRIVING')) {
    return 'Traffic';
  }
  if (chargeUpper.includes('WARRANT') || chargeUpper.includes('VOP') || chargeUpper.includes('VIOLATION')) {
    return 'Warrant';
  }
  
  return 'Other';
}

/**
 * Return empty statistics object
 * @returns {Object} Empty stats object
 */
function getEmptyStats() {
  return {
    total: 0,
    male: 0,
    female: 0,
    avgBond: 0,
    crimes: {}
  };
}
