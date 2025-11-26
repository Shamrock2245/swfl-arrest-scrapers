// Universal Booking Form Bookmarklet - County Agnostic
// Works across all 7 counties: Lee, Collier, Hendry, Charlotte, Manatee, Sarasota, Hillsborough

javascript:(function(){
  const formUrl = 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec';
  
  // ========================================================================
  // SMART DATA EXTRACTION - Works across all county websites
  // ========================================================================
  
  /**
   * Extract data using multiple selector strategies
   */
  function smartExtract(keywords, fallbackSelectors = []) {
    // Try exact text match in labels/headers
    for (const keyword of keywords) {
      const regex = new RegExp(keyword, 'i');
      
      // Try table cells (common in Revize sites)
      const cells = document.querySelectorAll('td, th');
      for (let i = 0; i < cells.length; i++) {
        if (regex.test(cells[i].textContent)) {
          const nextCell = cells[i].nextElementSibling;
          if (nextCell) {
            const text = nextCell.textContent.trim();
            if (text && text.length > 0) return text;
          }
        }
      }
      
      // Try definition lists
      const dts = document.querySelectorAll('dt');
      for (const dt of dts) {
        if (regex.test(dt.textContent)) {
          const dd = dt.nextElementSibling;
          if (dd && dd.tagName === 'DD') {
            const text = dd.textContent.trim();
            if (text && text.length > 0) return text;
          }
        }
      }
      
      // Try labeled divs/spans
      const labels = document.querySelectorAll('label, .label, [class*="label"]');
      for (const label of labels) {
        if (regex.test(label.textContent)) {
          const parent = label.parentElement;
          const text = parent.textContent.replace(label.textContent, '').trim();
          if (text && text.length > 0) return text;
        }
      }
    }
    
    // Try fallback CSS selectors
    for (const selector of fallbackSelectors) {
      const el = document.querySelector(selector);
      if (el) {
        const text = el.textContent.trim();
        if (text && text.length > 0) return text;
      }
    }
    
    return '';
  }
  
  /**
   * Extract date in MM/DD/YYYY format
   */
  function extractDate(text) {
    if (!text) return '';
    const match = text.match(/(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
    if (match) {
      return `${match[1].padStart(2, '0')}/${match[2].padStart(2, '0')}/${match[3]}`;
    }
    return '';
  }
  
  /**
   * Extract bond amount (remove non-numeric except $ and .)
   */
  function extractBond(text) {
    if (!text) return '';
    const match = text.match(/\$?[\d,]+\.?\d*/);
    if (match) {
      return match[0].replace(/,/g, '');
    }
    return '';
  }
  
  /**
   * Extract all charges from page
   */
  function extractCharges() {
    const chargeKeywords = ['charge', 'offense', 'violation', 'statute'];
    const charges = [];
    
    // Try table rows
    const rows = document.querySelectorAll('tr');
    rows.forEach(row => {
      const cells = row.querySelectorAll('td');
      if (cells.length >= 1) {
        const text = cells[0].textContent.trim();
        // Check if this looks like a charge (has statute number or common charge words)
        if (text.length > 10 && (
          /\d{3,}/.test(text) || 
          /DUI|THEFT|BATTERY|ASSAULT|DRUG|WARRANT/i.test(text)
        )) {
          charges.push(text);
        }
      }
    });
    
    // Try list items
    const listItems = document.querySelectorAll('li');
    listItems.forEach(li => {
      const text = li.textContent.trim();
      if (text.length > 10 && /\d{3,}/.test(text)) {
        charges.push(text);
      }
    });
    
    // If no charges found, try generic extraction
    if (charges.length === 0) {
      const chargeText = smartExtract(chargeKeywords, [
        '[class*="charge"]',
        '[class*="offense"]',
        '[id*="charge"]'
      ]);
      if (chargeText) charges.push(chargeText);
    }
    
    return charges.join('; ');
  }
  
  // ========================================================================
  // EXTRACT DATA FROM CURRENT PAGE
  // ========================================================================
  
  const bookingNumber = smartExtract(
    ['booking number', 'booking #', 'booking id', 'inmate id', 'inmate number'],
    ['[class*="booking"]', '[id*="booking"]', '.inmate-id']
  );
  
  const fullName = smartExtract(
    ['name', 'inmate name', 'defendant'],
    ['h1', 'h2', '[class*="name"]', '.inmate-name']
  );
  
  const dob = extractDate(smartExtract(
    ['date of birth', 'dob', 'birth date'],
    ['[class*="dob"]', '[class*="birth"]']
  ));
  
  const sex = smartExtract(
    ['sex', 'gender'],
    ['[class*="sex"]', '[class*="gender"]']
  ).substring(0, 1).toUpperCase();
  
  const race = smartExtract(
    ['race', 'ethnicity'],
    ['[class*="race"]']
  ).substring(0, 1).toUpperCase();
  
  const arrestDate = extractDate(smartExtract(
    ['arrest date', 'date arrested'],
    ['[class*="arrest-date"]']
  ));
  
  const bookingDate = extractDate(smartExtract(
    ['booking date', 'date booked', 'booked'],
    ['[class*="booking-date"]']
  ));
  
  const agency = smartExtract(
    ['agency', 'arresting agency', 'department'],
    ['[class*="agency"]']
  );
  
  const address = smartExtract(
    ['address', 'street', 'residence'],
    ['[class*="address"]']
  );
  
  const city = smartExtract(
    ['city', 'town'],
    ['[class*="city"]']
  );
  
  const state = smartExtract(
    ['state'],
    ['[class*="state"]']
  ) || 'FL';
  
  const zipcode = smartExtract(
    ['zip', 'zipcode', 'postal'],
    ['[class*="zip"]']
  );
  
  const charges = extractCharges();
  
  const bondAmount = extractBond(smartExtract(
    ['bond amount', 'bond', 'bail amount', 'bail'],
    ['[class*="bond"]', '[class*="bail"]']
  ));
  
  const bondType = smartExtract(
    ['bond type', 'bail type', 'type of bond'],
    ['[class*="bond-type"]']
  );
  
  const status = smartExtract(
    ['status', 'custody status'],
    ['[class*="status"]']
  );
  
  const courtDate = extractDate(smartExtract(
    ['court date', 'next court', 'appearance date'],
    ['[class*="court-date"]']
  ));
  
  const caseNumber = smartExtract(
    ['case number', 'case #', 'case id'],
    ['[class*="case"]']
  );
  
  // Parse name (handle "LAST, FIRST" format)
  let firstName = '';
  let lastName = '';
  
  if (fullName.includes(',')) {
    const parts = fullName.split(',').map(s => s.trim());
    lastName = parts[0];
    firstName = parts[1]?.split(' ')[0] || '';
  } else {
    const parts = fullName.split(' ');
    firstName = parts[0] || '';
    lastName = parts[parts.length - 1] || '';
  }
  
  // Detect county from URL
  const url = window.location.href.toLowerCase();
  let county = '';
  if (url.includes('lee')) county = 'Lee';
  else if (url.includes('collier')) county = 'Collier';
  else if (url.includes('hendry')) county = 'Hendry';
  else if (url.includes('charlotte')) county = 'Charlotte';
  else if (url.includes('manatee')) county = 'Manatee';
  else if (url.includes('sarasota')) county = 'Sarasota';
  else if (url.includes('hillsborough') || url.includes('hcso')) county = 'Hillsborough';
  
  // ========================================================================
  // BUILD URL AND OPEN FORM
  // ========================================================================
  
  const params = new URLSearchParams({
    bookingNumber,
    firstName,
    lastName,
    dob,
    sex,
    race,
    arrestDate,
    bookingDate,
    agency,
    address,
    city,
    state,
    zipcode,
    charges,
    bondAmount,
    bondType,
    status,
    courtDate,
    caseNumber,
    county
  });
  
  // Remove empty parameters
  for (const [key, value] of Array.from(params.entries())) {
    if (!value || value.trim() === '') {
      params.delete(key);
    }
  }
  
  // Open form in new window
  const finalUrl = `${formUrl}?${params.toString()}`;
  
  // Debug: Show extracted data
  console.log('Extracted Data:', {
    bookingNumber,
    fullName: `${firstName} ${lastName}`,
    dob,
    sex,
    race,
    charges,
    bondAmount,
    county
  });
  
  // Open form
  window.open(finalUrl, 'BookingForm', 'width=900,height=700,scrollbars=yes,resizable=yes');
  
})();
