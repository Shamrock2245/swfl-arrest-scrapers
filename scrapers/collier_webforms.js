// scrapers/collier_webforms.js
// Collier County ASP.NET WebForms scraper - handles Searchmobile.aspx with VIEWSTATE

import fetch from 'node-fetch';
import { normalizeRecord } from "../normalizers/normalize.js";
import {
  upsertRecords,
  mirrorQualifiedToDashboard,
  logIngestion,
} from "../writers/sheets.js";
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const config = JSON.parse(
  readFileSync(join(__dirname, "../config/counties.json"), "utf8")
).collier;

// URLs from Charles Proxy capture
const SEARCH_URL = 'https://ww2.colliersheriff.org/arrestersearch/Searchmobile.aspx';
const RESULTS_URL = 'https://ww2.colliersheriff.org/arrestersearch/SearchResults.aspx';

// Mobile User-Agent (iPhone Safari)
const USER_AGENT = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

/**
 * Main entry point
 */
export async function runCollierWebForms() {
  const startTime = Date.now();
  console.log("═══════════════════════════════════════");
  console.log("🚦 Starting Collier County WebForms Scraper");
  console.log("═══════════════════════════════════════");

  try {
    // Step 1: GET the search form
    console.log(`📡 GET: ${SEARCH_URL}`);
    const getResp = await fetch(SEARCH_URL, {
      method: 'GET',
      headers: {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
      }
    });

    if (!getResp.ok) {
      throw new Error(`GET failed with status ${getResp.status}`);
    }

    const getHtml = await getResp.text();
    console.log(`✅ GET successful (${getResp.status})`);

    // Step 2: Extract cookies
    const cookies = extractCookies(getResp);
    console.log(`🍪 Extracted ${cookies.length} cookies`);

    // Step 3: Parse form inputs
    const formData = extractFormInputs(getHtml);
    console.log(`📋 Extracted ${Object.keys(formData).length} form inputs`);

    // Step 4: Apply "Today's Arrests" search
    applyTodaysArrestsSearch(formData);

    // Step 5: POST the search
    console.log(`📡 POST: ${SEARCH_URL}`);
    const postResp = await fetch(SEARCH_URL, {
      method: 'POST',
      headers: {
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': cookies.join('; '),
        'Referer': SEARCH_URL,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Origin': 'https://ww2.colliersheriff.org'
      },
      body: new URLSearchParams(formData).toString(),
      redirect: 'follow'
    });

    if (!postResp.ok && postResp.status !== 302) {
      throw new Error(`POST failed with status ${postResp.status}`);
    }

    const resultsHtml = await postResp.text();
    console.log(`✅ POST successful (${postResp.status})`);

    // Step 6: Parse the results table
    const records = parseResultsTable(resultsHtml);
    console.log(`📊 Extracted ${records.length} raw records`);

    // Step 7: Normalize records
    const normalized = [];
    for (const raw of records) {
      try {
        const record = normalizeRecord(raw, "COLLIER", SEARCH_URL);
        if (record?.booking_id) {
          normalized.push(record);
          console.log(`   ✅ ${record.full_name_last_first || raw.name || "(no name)"}`);
        }
      } catch (e) {
        console.error(`   ⚠️  Normalization failed:`, e?.message || e);
      }
    }

    // Step 8: Write to Google Sheets
    console.log(`\n📊 Parsed ${normalized.length} valid records`);
    if (normalized.length > 0) {
      const result = await upsertRecords(config.sheetName, normalized);
      console.log(
        `✅ Inserted: ${result.inserted}, Updated: ${result.updated}`
      );
      await mirrorQualifiedToDashboard(normalized);
    }

    await logIngestion("COLLIER", true, normalized.length, startTime);
    console.log("✅ Finished Collier WebForms successfully.");
    console.log("═══════════════════════════════════════\n");
    return { success: true, count: normalized.length };

  } catch (error) {
    console.error("❌ Fatal error:", error?.message || error);
    if (error?.stack) console.error(error.stack);
    await logIngestion(
      "COLLIER",
      false,
      0,
      startTime,
      String(error?.message || error)
    );
    throw error;
  }
}

/**
 * Extract cookies from response headers
 */
function extractCookies(response) {
  const cookies = [];
  const setCookieHeaders = response.headers.raw()['set-cookie'] || [];
  
  for (const cookieHeader of setCookieHeaders) {
    const cookieValue = cookieHeader.split(';')[0].trim();
    if (cookieValue) {
      cookies.push(cookieValue);
    }
  }
  
  return cookies;
}

/**
 * Extract all form inputs from HTML
 */
function extractFormInputs(html) {
  const inputs = {};
  
  // Extract <input> tags
  const inputRegex = /<input\s+([^>]*?)(?:\/?>|>)/gi;
  let match;
  
  while ((match = inputRegex.exec(html)) !== null) {
    const inputTag = match[1];
    
    // Extract name
    const nameMatch = /name=["']([^"']+)["']/i.exec(inputTag);
    if (!nameMatch) continue;
    
    const name = nameMatch[1];
    
    // Extract value
    const valueMatch = /value=["']([^"]*)["']/i.exec(inputTag);
    const value = valueMatch ? decodeHtmlEntities(valueMatch[1]) : '';
    
    inputs[name] = value;
  }
  
  // Extract <textarea> tags
  const textareaRegex = /<textarea\s+([^>]*?)>(.*?)<\/textarea>/gi;
  while ((match = textareaRegex.exec(html)) !== null) {
    const textareaTag = match[1];
    const textareaContent = match[2];
    
    const nameMatch = /name=["']([^"']+)["']/i.exec(textareaTag);
    if (!nameMatch) continue;
    
    const name = nameMatch[1];
    inputs[name] = decodeHtmlEntities(textareaContent);
  }
  
  return inputs;
}

/**
 * Apply "Today's Arrests" search parameters
 */
function applyTodaysArrestsSearch(formData) {
  // TODO: Update these values based on actual Charles Proxy capture
  // For now, we'll leave the form mostly as-is and just trigger the search
  
  // Clear any pre-filled search fields
  if ('txtFirstName' in formData) formData.txtFirstName = '';
  if ('txtLastName' in formData) formData.txtLastName = '';
  
  // Set the search button
  if ('btnSearch' in formData) {
    formData.btnSearch = 'Search';
  }
  
  // If there's a "Today's Arrests" toggle, set it
  // Update this based on Charles capture
  if ('brdTodayArrests_ClientState' in formData) {
    formData.brdTodayArrests_ClientState = '{"value":"0"}';
  }
  
  console.log('   📅 Applied "Today\'s Arrests" search parameters');
}

/**
 * Parse the HTML results table
 */
function parseResultsTable(html) {
  const records = [];
  
  // Find the first <table>...</table>
  const tableMatch = /<table[^>]*?>([\s\S]*?)<\/table>/i.exec(html);
  
  if (!tableMatch) {
    console.warn('⚠️  No table found in results HTML');
    return records;
  }
  
  const tableHtml = tableMatch[1];
  
  // Extract all <tr>...</tr> blocks
  const trRegex = /<tr[^>]*?>([\s\S]*?)<\/tr>/gi;
  let trMatch;
  let headerRow = null;
  
  while ((trMatch = trRegex.exec(tableHtml)) !== null) {
    const rowHtml = trMatch[1];
    const cells = [];
    
    // Extract all <td> and <th> cells
    const cellRegex = /<t[hd][^>]*?>([\s\S]*?)<\/t[hd]>/gi;
    let cellMatch;
    
    while ((cellMatch = cellRegex.exec(rowHtml)) !== null) {
      let cellContent = cellMatch[1];
      
      // Convert <br> to newlines
      cellContent = cellContent.replace(/<br\s*\/?>/gi, '\n');
      
      // Strip HTML tags
      cellContent = cellContent.replace(/<[^>]+>/g, '');
      
      // Decode entities
      cellContent = decodeHtmlEntities(cellContent);
      
      // Trim
      cellContent = cellContent.trim();
      
      cells.push(cellContent);
    }
    
    // Skip empty rows
    if (cells.length === 0 || cells.every(c => c === '')) continue;
    
    // First non-empty row is the header
    if (!headerRow) {
      headerRow = cells;
      continue;
    }
    
    // Map cells to header to create record object
    const record = {};
    for (let i = 0; i < cells.length && i < headerRow.length; i++) {
      const key = headerRow[i].toLowerCase().replace(/\s+/g, '_');
      record[key] = cells[i];
    }
    
    // Map common field names
    if (record.name) record.name = record.name;
    if (record.booking_number || record['booking_#']) {
      record.bookingNumber = record.booking_number || record['booking_#'];
    }
    if (record.dob || record.date_of_birth) {
      record.dob = record.dob || record.date_of_birth;
    }
    if (record.arrest_date) {
      record.bookingDate = record.arrest_date;
    }
    
    records.push(record);
  }
  
  return records;
}

/**
 * Decode HTML entities
 */
function decodeHtmlEntities(str) {
  if (!str) return '';
  
  return str
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'")
    .replace(/&apos;/g, "'")
    .replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(dec))
    .replace(/&#x([0-9A-Fa-f]+);/g, (match, hex) => String.fromCharCode(parseInt(hex, 16)));
}

/* ----------------------- direct-run support ----------------------- */

if (import.meta.url === `file://${process.argv[1]}`) {
  runCollierWebForms().catch((error) => {
    console.error("Fatal error:", error);
    process.exit(1);
  });
}

export default runCollierWebForms;
