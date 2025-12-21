/**
 * Court Email Processor for Shamrock Bail Bonds
 * 
 * Automatically processes court date and forfeiture emails from shamrockbailoffice@gmail.com
 * Creates calendar events in shamrockbailoffice@gmail.com calendar (shared with admin@shamrockbailbonds.biz)
 * Posts notifications to Slack channels
 * 
 * Author: Shamrock Bail Bonds
 * Last Updated: December 10, 2025
 * Version: 2.1 - Fixed for shamrockbailoffice@gmail.com
 */

// ============================================================================
// CONFIGURATION - FIXED FOR SHAMROCKBAILOFFICE@GMAIL.COM
// ============================================================================

const CONFIG = {
  // Email configuration - uses current account
  emailAccount: Session.getActiveUser().getEmail(),  // ← FIXED: Uses shamrockbailoffice@gmail.com
  
  // Calendar configuration - uses current account's calendar
  calendarId: Session.getActiveUser().getEmail(),  // ← FIXED: Creates events in shamrockbailoffice@gmail.com calendar
  
  // Slack webhook URLs (add these after creating webhooks)
  slackWebhooks: {
    courtDates: '', // Add webhook URL for #court-dates channel
    forfeitures: ''  // Add webhook URL for #forfeitures channel
  },
  
  // Email whitelist - accepts emails from county clerk offices
  emailWhitelist: {
    // Specific senders
    specific: [
      'infocriminalbonds@leeclerk.org',
      'automail@leeclerk.org'
    ],
    
    // Wildcard domains (any sender from these domains)
    domains: [
      'leeclerk.org',
      'collierclerk.com',
      'hendryso.org',
      'charlotteclerk.com',
      'manateeclerk.com',
      'sarasotaclerk.com',
      'desotoclerk.com',
      'hillsboroughclerk.com'
    ],
    
    // Pattern matching (any county .org or .gov)
    patterns: [
      /.*clerk.*\.org$/i,
      /.*clerk.*\.gov$/i,
      /.*county.*\.org$/i,
      /.*county.*\.gov$/i
    ]
  },
  
  // Processing settings
  maxEmailsPerRun: 10,                    // Process up to 10 emails per run (to avoid timeout)
  batchSize: 10,                          // Process 10 emails per batch
  maxExecutionTime: 300000,               // 5 minutes (300 seconds) - leave 1 min buffer
  lookbackDays: 30,                       // Look back 30 days for unprocessed emails
  historicalStartDate: '2025-06-01',      // Start date for historical processing (June 2025)
  skipAlreadyProcessed: true,             // Skip emails that already have processing labels
  preventDuplicates: true,                // Check for existing calendar events before creating
  
  // Script properties keys for resume capability
  scriptPropertyKeys: {
    lastProcessedIndex: 'LAST_PROCESSED_INDEX',
    totalEmails: 'TOTAL_EMAILS_TO_PROCESS',
    processingStartTime: 'PROCESSING_START_TIME'
  },
  
  // Gmail labels
  labels: {
    courtDate: 'Processed - Court Date',
    forfeiture: 'Processed - Forfeiture',
    error: 'Processing Error'
  },
  
  // Calendar event colors
  colors: {
    courtDate: CalendarApp.EventColor.BLUE,
    forfeitureDate: CalendarApp.EventColor.RED,
    forfeitureReceived: CalendarApp.EventColor.ORANGE
  },
  
  // Subject line keywords
  keywords: {
    courtDate: ['SERVICE OF COURT DOCUMENT for Case Number', 'Notice of Appearance'],
    forfeiture: ['Notice of Forfeiture', 'FORFEITURE']
  }
};

// ============================================================================
// MAIN PROCESSING FUNCTIONS
// ============================================================================

/**
 * Main function to process court emails with batch processing
 * Can be run manually or via trigger
 * Automatically processes in batches to avoid timeout
 */
function processCourtEmails() {
  const startTime = new Date().getTime();
  
  try {
    Logger.log('🚀 Starting court email processor...');
    Logger.log(`📧 Email account: ${CONFIG.emailAccount}`);
    Logger.log(`📅 Calendar: ${CONFIG.calendarId}`);
    
    // Get unprocessed emails from the last lookback period
    const emails = getUnprocessedEmails(CONFIG.lookbackDays);
    
    Logger.log(`📧 Found ${emails.length} unprocessed emails`);
    
    if (emails.length === 0) {
      Logger.log('✅ No new emails to process');
      return {
        processed: 0,
        skipped: 0,
        errors: 0
      };
    }
    
    // Process emails in batch (limited to avoid timeout)
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    const batchSize = Math.min(CONFIG.batchSize, emails.length);
    Logger.log(`📦 Processing batch of ${batchSize} emails`);
    
    for (let i = 0; i < batchSize; i++) {
      // Check if we're approaching timeout
      const elapsed = new Date().getTime() - startTime;
      if (elapsed > CONFIG.maxExecutionTime) {
        Logger.log(`⏱️  Approaching timeout, stopping at ${i}/${batchSize}`);
        break;
      }
      
      const message = emails[i];
      
      try {
        Logger.log(`\n[${i + 1}/${batchSize}] Processing email: ${message.getSubject()}`);
        
        const result = processEmail(message);
        
        if (result.success) {
          processed++;
          Logger.log(`✅ Successfully processed`);
        } else if (result.skipped) {
          skipped++;
          Logger.log(`⏭️  Skipped: ${result.reason}`);
        } else {
          errors++;
          Logger.log(`❌ Error: ${result.error}`);
        }
      } catch (error) {
        errors++;
        Logger.log(`❌ Error processing email: ${error.message}`);
        labelEmail(message, CONFIG.labels.error);
      }
    }
    
    // Log summary
    const remaining = emails.length - batchSize;
    Logger.log(`\n📊 Batch processing complete:`);
    Logger.log(`   ✅ Processed: ${processed}`);
    Logger.log(`   ⏭️  Skipped: ${skipped}`);
    Logger.log(`   ❌ Errors: ${errors}`);
    
    if (remaining > 0) {
      Logger.log(`\n⏳ ${remaining} emails remaining`);
      Logger.log(`💡 Run this function again to process the next batch`);
    } else {
      Logger.log(`\n🎉 All emails processed!`);
    }
    
    return {
      processed,
      skipped,
      errors,
      remaining
    };
    
  } catch (error) {
    Logger.log(`❌ Fatal error in processCourtEmails: ${error.message}`);
    throw error;
  }
}

/**
 * Process historical emails from configured start date to now
 * Run this ONCE after initial setup to catch up on past emails
 */
function processHistoricalEmails() {
  const ui = SpreadsheetApp.getUi();
  
  // Confirm with user
  const response = ui.alert(
    'Process Historical Emails',
    `This will process ALL court emails from ${CONFIG.historicalStartDate} to today.\n\n` +
    `This may take 5-15 minutes depending on email volume.\n\n` +
    `Continue?`,
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    Logger.log('❌ Historical processing cancelled by user');
    return;
  }
  
  try {
    Logger.log(`🔄 Starting historical email processing...`);
    Logger.log(`📅 Date range: ${CONFIG.historicalStartDate} to ${new Date().toISOString().split('T')[0]}`);
    
    // Get historical emails
    const emails = getHistoricalEmails();
    
    Logger.log(`📧 Found ${emails.length} historical emails`);
    
    if (emails.length === 0) {
      ui.alert('No Historical Emails Found', 'No court emails found in the specified date range.', ui.ButtonSet.OK);
      return;
    }
    
    // Process emails
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    emails.forEach((message, index) => {
      try {
        // Show progress every 10 emails
        if ((index + 1) % 10 === 0) {
          Logger.log(`📊 Progress: ${index + 1}/${emails.length} emails processed`);
        }
        
        const result = processEmail(message);
        
        if (result.success) {
          processed++;
        } else if (result.skipped) {
          skipped++;
        } else {
          errors++;
        }
      } catch (error) {
        errors++;
        Logger.log(`❌ Error processing email ${index + 1}: ${error.message}`);
        labelEmail(message, CONFIG.labels.error);
      }
    });
    
    // Show summary
    const summary = `
📊 Historical Processing Complete!

✅ Processed: ${processed}
⏭️  Skipped: ${skipped}
❌ Errors: ${errors}

Total emails checked: ${emails.length}
    `.trim();
    
    Logger.log(`\n${summary}`);
    ui.alert('Historical Processing Complete', summary, ui.ButtonSet.OK);
    
  } catch (error) {
    Logger.log(`❌ Fatal error in processHistoricalEmails: ${error.message}`);
    ui.alert('Error', `Failed to process historical emails: ${error.message}`, ui.ButtonSet.OK);
    throw error;
  }
}

/**
 * Process custom date range
 */
function processDateRange() {
  const ui = SpreadsheetApp.getUi();
  
  // Get start date
  const startResponse = ui.prompt(
    'Process Custom Date Range',
    'Enter start date (YYYY-MM-DD):',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (startResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const startDate = startResponse.getResponseText().trim();
  
  if (!isValidDate(startDate)) {
    ui.alert('Invalid Date', 'Please enter date in YYYY-MM-DD format (e.g., 2025-01-01)', ui.ButtonSet.OK);
    return;
  }
  
  // Get end date
  const endResponse = ui.prompt(
    'Process Custom Date Range',
    'Enter end date (YYYY-MM-DD):',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (endResponse.getSelectedButton() !== ui.Button.OK) {
    return;
  }
  
  const endDate = endResponse.getResponseText().trim();
  
  if (!isValidDate(endDate)) {
    ui.alert('Invalid Date', 'Please enter date in YYYY-MM-DD format (e.g., 2025-12-31)', ui.ButtonSet.OK);
    return;
  }
  
  // Process the date range
  processCustomDateRange(startDate, endDate);
}

/**
 * Process emails in custom date range
 */
function processCustomDateRange(startDate, endDate) {
  const ui = SpreadsheetApp.getUi();
  
  try {
    Logger.log(`🔄 Processing custom date range: ${startDate} to ${endDate}`);
    
    // Build search query
    const query = `has:attachment after:${startDate} before:${endDate}`;
    const threads = GmailApp.search(query, 0, 500);
    const messages = [];
    
    threads.forEach(thread => {
      thread.getMessages().forEach(message => {
        if (isFromWhitelistedSender(message.getFrom())) {
          messages.push(message);
        }
      });
    });
    
    Logger.log(`📧 Found ${messages.length} emails in date range`);
    
    if (messages.length === 0) {
      ui.alert('No Emails Found', `No court emails found between ${startDate} and ${endDate}.`, ui.ButtonSet.OK);
      return;
    }
    
    // Process emails
    let processed = 0;
    let skipped = 0;
    let errors = 0;
    
    messages.forEach((message, index) => {
      try {
        const result = processEmail(message);
        
        if (result.success) {
          processed++;
        } else if (result.skipped) {
          skipped++;
        } else {
          errors++;
        }
      } catch (error) {
        errors++;
        Logger.log(`❌ Error processing email ${index + 1}: ${error.message}`);
        labelEmail(message, CONFIG.labels.error);
      }
    });
    
    // Show summary
    const summary = `
📊 Date Range Processing Complete!

Date Range: ${startDate} to ${endDate}

✅ Processed: ${processed}
⏭️  Skipped: ${skipped}
❌ Errors: ${errors}

Total emails checked: ${messages.length}
    `.trim();
    
    Logger.log(`\n${summary}`);
    ui.alert('Processing Complete', summary, ui.ButtonSet.OK);
    
  } catch (error) {
    Logger.log(`❌ Fatal error in processCustomDateRange: ${error.message}`);
    ui.alert('Error', `Failed to process date range: ${error.message}`, ui.ButtonSet.OK);
    throw error;
  }
}

// ============================================================================
// EMAIL RETRIEVAL FUNCTIONS
// ============================================================================

/**
 * Get unprocessed emails from the last N days
 */
function getUnprocessedEmails(days) {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - days);
    const dateStr = Utilities.formatDate(cutoffDate, Session.getScriptTimeZone(), 'yyyy/MM/dd');
    
    // Search for emails with attachments after cutoff date
    const query = `has:attachment after:${dateStr}`;
    const threads = GmailApp.search(query, 0, CONFIG.maxEmailsPerRun);
    
    const messages = [];
    
    threads.forEach(thread => {
      thread.getMessages().forEach(message => {
        // Check if from whitelisted sender
        if (!isFromWhitelistedSender(message.getFrom())) {
          return;
        }
        
        // Check if already processed
        if (CONFIG.skipAlreadyProcessed && isAlreadyProcessed(message)) {
          return;
        }
        
        // Check if court-related
        if (isCourtEmail(message)) {
          messages.push(message);
        }
      });
    });
    
    return messages;
    
  } catch (error) {
    Logger.log(`❌ Error getting unprocessed emails: ${error.message}`);
    throw error;
  }
}

/**
 * Get historical emails from configured start date with proper pagination
 * Gmail search() is limited to 500 results, so we paginate to get ALL emails
 */
function getHistoricalEmails() {
  try {
    const startDate = CONFIG.historicalStartDate;
    const today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy/MM/dd');
    
    Logger.log(`📅 Searching for emails from ${startDate} to ${today}`);
    
    // Search for emails with attachments in date range
    const query = `has:attachment after:${startDate} before:${today}`;
    
    const messages = [];
    let start = 0;
    const batchSize = 500; // Gmail's max per search
    let hasMore = true;
    
    // Paginate through all emails
    while (hasMore) {
      Logger.log(`📦 Fetching batch starting at ${start}...`);
      
      const threads = GmailApp.search(query, start, batchSize);
      
      if (threads.length === 0) {
        hasMore = false;
        break;
      }
      
      Logger.log(`   Found ${threads.length} threads in this batch`);
      
      threads.forEach(thread => {
        thread.getMessages().forEach(message => {
          // Check if from whitelisted sender
          if (!isFromWhitelistedSender(message.getFrom())) {
            return;
          }
          
          // Check if already processed (optional)
          if (CONFIG.skipAlreadyProcessed && isAlreadyProcessed(message)) {
            return;
          }
          
          // Check if court-related
          if (isCourtEmail(message)) {
            messages.push(message);
          }
        });
      });
      
      // Move to next batch
      start += batchSize;
      
      // If we got fewer than batchSize, we're done
      if (threads.length < batchSize) {
        hasMore = false;
      }
    }
    
    Logger.log(`✅ Total court emails found: ${messages.length}`);
    
    // Sort by date (oldest first)
    messages.sort((a, b) => a.getDate() - b.getDate());
    
    return messages;
    
  } catch (error) {
    Logger.log(`❌ Error getting historical emails: ${error.message}`);
    throw error;
  }
}

// ============================================================================
// EMAIL VALIDATION FUNCTIONS
// ============================================================================

/**
 * Check if email is from whitelisted sender
 */
function isFromWhitelistedSender(from) {
  const fromLower = from.toLowerCase();
  
  // Check specific senders
  for (const sender of CONFIG.emailWhitelist.specific) {
    if (fromLower.includes(sender.toLowerCase())) {
      return true;
    }
  }
  
  // Check domains
  for (const domain of CONFIG.emailWhitelist.domains) {
    if (fromLower.includes(`@${domain.toLowerCase()}`)) {
      return true;
    }
  }
  
  // Check patterns
  for (const pattern of CONFIG.emailWhitelist.patterns) {
    // Extract email address from "Name <email@domain.com>" format
    const emailMatch = from.match(/<(.+?)>/);
    const email = emailMatch ? emailMatch[1] : from;
    
    if (pattern.test(email)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Check if email is court-related
 */
function isCourtEmail(message) {
  const subject = message.getSubject();
  
  // Check for court date keywords
  for (const keyword of CONFIG.keywords.courtDate) {
    if (subject.includes(keyword)) {
      return true;
    }
  }
  
  // Check for forfeiture keywords
  for (const keyword of CONFIG.keywords.forfeiture) {
    if (subject.includes(keyword)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Check if email has already been processed
 */
function isAlreadyProcessed(message) {
  const thread = message.getThread();
  const labels = thread.getLabels();
  
  for (const label of labels) {
    const labelName = label.getName();
    if (labelName === CONFIG.labels.courtDate || 
        labelName === CONFIG.labels.forfeiture ||
        labelName === CONFIG.labels.error) {
      return true;
    }
  }
  
  return false;
}

/**
 * Validate date format (YYYY-MM-DD)
 */
function isValidDate(dateString) {
  const regex = /^\d{4}-\d{2}-\d{2}$/;
  if (!regex.test(dateString)) {
    return false;
  }
  
  const date = new Date(dateString);
  return date instanceof Date && !isNaN(date);
}

// ============================================================================
// EMAIL PROCESSING FUNCTIONS
// ============================================================================

/**
 * Process a single email
 */
function processEmail(message) {
  try {
    const subject = message.getSubject();
    
    // Determine email type
    const isForfeiture = CONFIG.keywords.forfeiture.some(keyword => subject.includes(keyword));
    
    if (isForfeiture) {
      return processForfeitureEmail(message);
    } else {
      return processCourtDateEmail(message);
    }
    
  } catch (error) {
    Logger.log(`❌ Error in processEmail: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Process court date email
 */
function processCourtDateEmail(message) {
  try {
    // Extract data from PDF attachment
    const data = extractCourtDateData(message);
    
    if (!data) {
      return {
        success: false,
        error: 'Could not extract data from PDF'
      };
    }
    
    // Create calendar event
    createCourtDateEvent(data);
    
    // Post to Slack
    if (CONFIG.slackWebhooks.courtDates) {
      postToSlack(CONFIG.slackWebhooks.courtDates, formatCourtDateSlackMessage(data));
    }
    
    // Label email
    labelEmail(message, CONFIG.labels.courtDate);
    
    return {
      success: true
    };
    
  } catch (error) {
    Logger.log(`❌ Error processing court date email: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

/**
 * Process forfeiture email
 */
function processForfeitureEmail(message) {
  try {
    // Extract data from PDF attachment
    const data = extractForfeitureData(message);
    
    if (!data) {
      return {
        success: false,
        error: 'Could not extract data from PDF'
      };
    }
    
    // Create calendar events (2 events: forfeiture date + received date)
    createForfeitureEvents(data);
    
    // Post to Slack
    if (CONFIG.slackWebhooks.forfeitures) {
      postToSlack(CONFIG.slackWebhooks.forfeitures, formatForfeitureSlackMessage(data));
    }
    
    // Label email
    labelEmail(message, CONFIG.labels.forfeiture);
    
    return {
      success: true
    };
    
  } catch (error) {
    Logger.log(`❌ Error processing forfeiture email: ${error.message}`);
    return {
      success: false,
      error: error.message
    };
  }
}

// ============================================================================
// DATA EXTRACTION FUNCTIONS
// ============================================================================

/**
 * Extract court date data from email body (FAST) + quick PDF time scan
 */
function extractCourtDateData(message) {
  try {
    const subject = message.getSubject();
    const body = message.getPlainBody();
    
    // Extract case number from subject line
    const caseMatch = subject.match(/(\d{2}-[A-Z]+-\d+)/i);
    const caseNumber = caseMatch ? caseMatch[1] : 'Unknown';
    
    // Extract defendant name from body
    // Looking for pattern: "Parties: [Name]" or "Defendant: [Name]"
    let defendant = 'Unknown';
    const defendantMatch = body.match(/(?:Parties|Defendant)[:\s]+([^\n]+)/i);
    if (defendantMatch) {
      defendant = defendantMatch[1].trim();
    }
    
    // Extract courtroom from body
    // Looking for pattern: "Courtroom 5-A" or "Courtroom: 5-A"
    let courtroom = 'Unknown';
    const courtroomMatch = body.match(/Courtroom[:\s]*([A-Z0-9-]+)/i);
    if (courtroomMatch) {
      courtroom = courtroomMatch[1];
    }
    
    // Extract court date from body or PDF
    let courtDateStr = null;
    const dateMatch = body.match(/(\d{1,2}\/\d{1,2}\/\d{4})/i);
    if (dateMatch) {
      courtDateStr = dateMatch[1];
    }
    
    // Quick scan PDF for time only (very fast)
    let courtTime = '09:00 AM'; // Default time if not found
    const attachments = message.getAttachments();
    
    for (const attachment of attachments) {
      if (attachment.getContentType() === 'application/pdf') {
        const timeFromPDF = extractTimeFromPDF(attachment);
        if (timeFromPDF) {
          courtTime = timeFromPDF;
          
          // Also try to get date from PDF if not in body
          if (!courtDateStr) {
            const pdfDateMatch = attachment.getDataAsString().match(/(\d{1,2}\/\d{1,2}\/\d{4})/i);
            if (pdfDateMatch) {
              courtDateStr = pdfDateMatch[1];
            }
          }
        }
        break; // Only check first PDF
      }
    }
    
    // Create court date object
    if (!courtDateStr) {
      Logger.log('⚠️  Could not extract court date');
      return null;
    }
    
    const courtDate = new Date(courtDateStr + ' ' + courtTime);
    
    // Extract bonds from body (if present)
    const bondMatches = [...body.matchAll(/Bond[\s#]*[:\s]*([A-Z0-9-]+)[^\$]*\$([0-9,]+)/gi)];
    const bonds = bondMatches.map(match => ({
      number: match[1],
      amount: match[2]
    }));
    
    // Extract charges from body (if present)
    const chargeMatches = [...body.matchAll(/Count[\s]+\d+[:\s]*([A-Z][A-Z\s\-\/]+?)(?:\n|$)/gi)];
    const charges = chargeMatches.map(match => match[1].trim()).filter(c => c.length > 5);
    
    Logger.log(`✅ Extracted: ${defendant}, ${caseNumber}, ${courtroom}, ${courtDateStr} ${courtTime}`);
    
    return {
      caseNumber,
      defendant,
      courtDate,
      courtroom,
      bonds,
      charges,
      emailDate: message.getDate()
    };
    
  } catch (error) {
    Logger.log(`❌ Error extracting court date data: ${error.message}`);
    return null;
  }
}

/**
 * Extract forfeiture data from PDF attachment
 */
function extractForfeitureData(message) {
  try {
    const attachments = message.getAttachments();
    
    for (const attachment of attachments) {
      if (attachment.getContentType() === 'application/pdf') {
        const pdfText = extractTextFromPDF(attachment);
        
        // Extract case number
        const caseMatch = pdfText.match(/Case Number[:\s]+(\d{2}-[A-Z]+-\d+)/i);
        const caseNumber = caseMatch ? caseMatch[1] : 'Unknown';
        
        // Extract defendant name
        const defendantMatch = pdfText.match(/vs[.\s]+(.+?)(?:\n|Shamrock)/i);
        const defendant = defendantMatch ? defendantMatch[1].trim() : 'Unknown';
        
        // Extract forfeiture date from "PLEASE TAKE NOTICE" section
        const forfeitureDateMatch = pdfText.match(/On\s+(\d{1,2}\/\d{1,2}\/\d{4})/i);
        const forfeitureDate = forfeitureDateMatch ? new Date(forfeitureDateMatch[1]) : null;
        
        // Extract received date from Certificate of Service
        const receivedDateMatch = pdfText.match(/(\d{1,2})\s+day\s+of\s+(\w+),\s+(\d{4})/i);
        let receivedDate = message.getDate();
        
        if (receivedDateMatch) {
          const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                            'July', 'August', 'September', 'October', 'November', 'December'];
          const month = monthNames.indexOf(receivedDateMatch[2]);
          receivedDate = new Date(receivedDateMatch[3], month, receivedDateMatch[1]);
        }
        
        // Extract bonds
        const bondMatches = [...pdfText.matchAll(/([A-Z0-9-]+)\s+\$([0-9,]+)/g)];
        const bonds = bondMatches.map(match => ({
          number: match[1],
          amount: match[2]
        }));
        
        // Extract insurer
        const insurerMatch = pdfText.match(/\[insurer\][^\n]*\n([^\n]+)/i);
        const insurer = insurerMatch ? insurerMatch[1].trim() : 'Unknown';
        
        return {
          caseNumber,
          defendant,
          forfeitureDate,
          receivedDate,
          bonds,
          insurer,
          emailDate: message.getDate()
        };
      }
    }
    
    return null;
    
  } catch (error) {
    Logger.log(`❌ Error extracting forfeiture data: ${error.message}`);
    return null;
  }
}

/**
 * Extract text from PDF attachment using DriveApp (no API needed)
 */
function extractTextFromPDF(attachment) {
  try {
    // Create temporary file in Drive
    const blob = attachment.copyBlob();
    const tempFolder = DriveApp.getRootFolder();
    const file = tempFolder.createFile(blob);
    
    // Get file ID
    const fileId = file.getId();
    
    // Convert to Google Doc to extract text
    const resource = {
      mimeType: 'application/vnd.google-apps.document'
    };
    
    const convertedFile = Drive.Files.copy(resource, fileId);
    const docId = convertedFile.id;
    
    // Get text from converted document
    const doc = DocumentApp.openById(docId);
    const text = doc.getBody().getText();
    
    // Clean up temporary files
    DriveApp.getFileById(fileId).setTrashed(true);
    DriveApp.getFileById(docId).setTrashed(true);
    
    return text;
    
  } catch (error) {
    Logger.log(`❌ Error extracting text from PDF: ${error.message}`);
    
    // Fallback: Try simple text extraction
    try {
      const pdfContent = attachment.getDataAsString();
      // Extract readable text from PDF string
      const textMatches = pdfContent.match(/[\x20-\x7E\s]{4,}/g);
      return textMatches ? textMatches.join(' ') : pdfContent;
    } catch (fallbackError) {
      Logger.log(`❌ Fallback also failed: ${fallbackError.message}`);
      return '';
    }
  }
}

// ============================================================================
// CALENDAR FUNCTIONS
// ============================================================================

/**
 * Create calendar event for court date
 */
function createCourtDateEvent(data) {
  try {
    const calendar = CalendarApp.getCalendarById(CONFIG.calendarId);
    
    if (!calendar) {
      throw new Error(`Calendar not found: ${CONFIG.calendarId}`);
    }
    
    // Create event title
    const title = `Court: ${data.defendant} - ${data.caseNumber}`;
    
    // Create event description
    const description = `
**Court Appearance**

**Defendant:** ${data.defendant}
**Case Number:** ${data.caseNumber}
**Courtroom:** ${data.courtroom}

**Bonds:**
${data.bonds.map(b => `- ${b.number}: $${b.amount}`).join('\n')}

**Charges:**
${data.charges.map((c, i) => `${i + 1}. ${c}`).join('\n')}

**Email received:** ${Utilities.formatDate(data.emailDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}
    `.trim();
    
    // Check for duplicate
    if (CONFIG.preventDuplicates) {
      const existing = calendar.getEventsForDay(data.courtDate);
      for (const event of existing) {
        if (event.getTitle() === title) {
          Logger.log(`⏭️  Calendar event already exists: ${title}`);
          return;
        }
      }
    }
    
    // Create event
    const event = calendar.createEvent(title, data.courtDate, data.courtDate, {
      description: description,
      location: `Courtroom ${data.courtroom}`
    });
    
    // Set color
    event.setColor(CONFIG.colors.courtDate);
    
    Logger.log(`📅 Created calendar event: ${title}`);
    
  } catch (error) {
    Logger.log(`❌ Error creating court date event: ${error.message}`);
    throw error;
  }
}

/**
 * Create calendar events for forfeiture (2 events)
 */
function createForfeitureEvents(data) {
  try {
    const calendar = CalendarApp.getCalendarById(CONFIG.calendarId);
    
    if (!calendar) {
      throw new Error(`Calendar not found: ${CONFIG.calendarId}`);
    }
    
    // Event 1: Forfeiture date (red)
    if (data.forfeitureDate) {
      const title1 = `⚠️ FORFEITURE: ${data.defendant} - ${data.caseNumber}`;
      
      const description1 = `
**Bond Forfeiture**

**Defendant:** ${data.defendant}
**Case Number:** ${data.caseNumber}
**Forfeiture Date:** ${Utilities.formatDate(data.forfeitureDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}

**Bonds:**
${data.bonds.map(b => `- ${b.number}: $${b.amount}`).join('\n')}

**Insurer:** ${data.insurer}

**Notice received:** ${Utilities.formatDate(data.receivedDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}
      `.trim();
      
      // Check for duplicate
      if (CONFIG.preventDuplicates) {
        const existing = calendar.getEventsForDay(data.forfeitureDate);
        for (const event of existing) {
          if (event.getTitle() === title1) {
            Logger.log(`⏭️  Calendar event already exists: ${title1}`);
            return;
          }
        }
      }
      
      const event1 = calendar.createAllDayEvent(title1, data.forfeitureDate, {
        description: description1
      });
      
      event1.setColor(CONFIG.colors.forfeitureDate);
      
      Logger.log(`📅 Created forfeiture date event: ${title1}`);
    }
    
    // Event 2: Received date (orange)
    const title2 = `📧 Forfeiture Notice Received: ${data.defendant} - ${data.caseNumber}`;
    
    const description2 = `
**Forfeiture Notice Received**

**Defendant:** ${data.defendant}
**Case Number:** ${data.caseNumber}
**Received Date:** ${Utilities.formatDate(data.receivedDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}
**Forfeiture Date:** ${data.forfeitureDate ? Utilities.formatDate(data.forfeitureDate, Session.getScriptTimeZone(), 'MM/dd/yyyy') : 'Unknown'}

**Bonds:**
${data.bonds.map(b => `- ${b.number}: $${b.amount}`).join('\n')}

**Insurer:** ${data.insurer}
    `.trim();
    
    const event2 = calendar.createAllDayEvent(title2, data.receivedDate, {
      description: description2
    });
    
    event2.setColor(CONFIG.colors.forfeitureReceived);
    
    Logger.log(`📅 Created received date event: ${title2}`);
    
  } catch (error) {
    Logger.log(`❌ Error creating forfeiture events: ${error.message}`);
    throw error;
  }
}

// ============================================================================
// SLACK FUNCTIONS
// ============================================================================

/**
 * Post message to Slack
 */
function postToSlack(webhookUrl, message) {
  try {
    if (!webhookUrl) {
      Logger.log('⏭️  Slack webhook not configured, skipping notification');
      return;
    }
    
    const payload = JSON.stringify(message);
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: payload
    };
    
    UrlFetchApp.fetch(webhookUrl, options);
    
    Logger.log('✅ Posted to Slack');
    
  } catch (error) {
    Logger.log(`❌ Error posting to Slack: ${error.message}`);
  }
}

/**
 * Format court date message for Slack
 */
function formatCourtDateSlackMessage(data) {
  return {
    text: `🏛️ New Court Date`,
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: '🏛️ New Court Date'
        }
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*Defendant:*\n${data.defendant}`
          },
          {
            type: 'mrkdwn',
            text: `*Case Number:*\n${data.caseNumber}`
          },
          {
            type: 'mrkdwn',
            text: `*Court Date:*\n${Utilities.formatDate(data.courtDate, Session.getScriptTimeZone(), 'MM/dd/yyyy hh:mm a')}`
          },
          {
            type: 'mrkdwn',
            text: `*Courtroom:*\n${data.courtroom}`
          }
        ]
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Bonds:*\n${data.bonds.map(b => `• ${b.number}: $${b.amount}`).join('\n')}`
        }
      }
    ]
  };
}

/**
 * Format forfeiture message for Slack
 */
function formatForfeitureSlackMessage(data) {
  return {
    text: `⚠️ FORFEITURE NOTICE`,
    blocks: [
      {
        type: 'header',
        text: {
          type: 'plain_text',
          text: '⚠️ FORFEITURE NOTICE'
        }
      },
      {
        type: 'section',
        fields: [
          {
            type: 'mrkdwn',
            text: `*Defendant:*\n${data.defendant}`
          },
          {
            type: 'mrkdwn',
            text: `*Case Number:*\n${data.caseNumber}`
          },
          {
            type: 'mrkdwn',
            text: `*Forfeiture Date:*\n${data.forfeitureDate ? Utilities.formatDate(data.forfeitureDate, Session.getScriptTimeZone(), 'MM/dd/yyyy') : 'Unknown'}`
          },
          {
            type: 'mrkdwn',
            text: `*Received Date:*\n${Utilities.formatDate(data.receivedDate, Session.getScriptTimeZone(), 'MM/dd/yyyy')}`
          }
        ]
      },
      {
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: `*Bonds:*\n${data.bonds.map(b => `• ${b.number}: $${b.amount}`).join('\n')}\n\n*Insurer:* ${data.insurer}`
        }
      }
    ]
  };
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Label email with specified label
 */
function labelEmail(message, labelName) {
  try {
    let label = GmailApp.getUserLabelByName(labelName);
    
    if (!label) {
      label = GmailApp.createLabel(labelName);
    }
    
    message.getThread().addLabel(label);
    
  } catch (error) {
    Logger.log(`❌ Error labeling email: ${error.message}`);
  }
}

/**
 * Show Slack configuration instructions
 */
function showSlackConfig() {
  const ui = SpreadsheetApp.getUi();
  
  const message = `
To enable Slack notifications:

1. Go to https://api.slack.com/apps
2. Create New App → "Shamrock Court Alerts"
3. Incoming Webhooks → Toggle ON
4. Add New Webhook → Select #court-dates
5. Copy webhook URL
6. Repeat for #forfeitures channel

Then update CONFIG.slackWebhooks in the script:

slackWebhooks: {
  courtDates: 'YOUR_WEBHOOK_URL',
  forfeitures: 'YOUR_WEBHOOK_URL'
}
  `.trim();
  
  ui.alert('Slack Configuration', message, ui.ButtonSet.OK);
}

/**
 * Show processing log
 */
function showProcessingLog() {
  const ui = SpreadsheetApp.getUi();
  const log = Logger.getLog();
  
  if (!log || log.trim() === '') {
    ui.alert('Processing Log', 'No processing log available. Run the processor first.', ui.ButtonSet.OK);
    return;
  }
  
  ui.alert('Processing Log', log, ui.ButtonSet.OK);
}
