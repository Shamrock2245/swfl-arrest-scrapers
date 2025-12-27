/**
 * ============================================================================
 * MCPServer.gs - Custom MCP Server for Shamrock Bail Bonds
 * ============================================================================
 * 
 * Exposes Google Apps Script backend functions as MCP tools for Manus integration.
 * Enables natural language control of the entire bail bond workflow.
 * 
 * Prerequisites:
 * - Install MCPApp library: 1TlX_L9COAriBlAYvrMLiRFQ5WVf1n0jChB6zHamq2TNwuSbVlI5sBUzh
 * - Set MCP_API_KEY in Script Properties
 * - Deploy as Web App (Execute as: Me, Access: Anyone)
 * 
 * Author: Shamrock Bail Bonds
 * Date: December 27, 2025
 * Version: 1.0.0
 */

// ============================================================================
// COMPONENT 1: MCP SERVER CONFIGURATION
// ============================================================================

/**
 * MCP Server entry point - handles all MCP requests from Manus
 * This is the doPost handler that receives JSON-RPC 2.0 requests
 */
function doPost(e) {
  try {
    // Validate API key for security
    const providedKey = extractApiKey_(e);
    const validKey = PropertiesService.getScriptProperties().getProperty('MCP_API_KEY');
    
    if (!validKey) {
      return createErrorResponse_('Server configuration error: MCP_API_KEY not set');
    }
    
    if (providedKey !== validKey) {
      return createErrorResponse_('Unauthorized: Invalid API key');
    }
    
    // Build MCP server object
    const object = {
      eventObject: e,
      serverResponse: getMCPServerResponse_(),
      functions: getMCPFunctions_()
    };
    
    // Use MCPApp library to handle protocol compliance
    return new MCPApp.mcpApp({ accessKey: validKey }).server(object);
    
  } catch (error) {
    Logger.log('MCP Server Error: ' + error.toString());
    return createErrorResponse_('Internal server error: ' + error.message);
  }
}

/**
 * Extract API key from request (supports multiple formats)
 */
function extractApiKey_(e) {
  // Try parameter
  if (e.parameter && e.parameter.apiKey) {
    return e.parameter.apiKey;
  }
  
  // Try POST data
  if (e.postData && e.postData.contents) {
    try {
      const data = JSON.parse(e.postData.contents);
      if (data.apiKey) return data.apiKey;
    } catch (err) {
      // Not JSON or no apiKey field
    }
  }
  
  // Try headers (if MCPApp passes them through)
  if (e.parameter && e.parameter.Authorization) {
    return e.parameter.Authorization.replace('Bearer ', '');
  }
  
  return null;
}

/**
 * Create error response in JSON-RPC 2.0 format
 */
function createErrorResponse_(message) {
  return ContentService.createTextOutput(JSON.stringify({
    jsonrpc: "2.0",
    error: {
      code: -32001,
      message: message
    }
  })).setMimeType(ContentService.MimeType.JSON);
}

/**
 * Define MCP server capabilities and metadata
 */
function getMCPServerResponse_() {
  return {
    // Response to "initialize" request
    initialize: {
      jsonrpc: "2.0",
      result: {
        protocolVersion: "2025-03-26",
        capabilities: {
          experimental: {},
          prompts: { listChanged: false },
          resources: { subscribe: false, listChanged: false },
          tools: { listChanged: false }
        },
        serverInfo: {
          name: "Shamrock Bail Bonds Automation Server",
          version: "1.0.0",
          description: "Complete bail bond workflow automation including scrapers, lead scoring, court email processing, SignNow integration, and Slack notifications"
        }
      }
    },
    
    // Response to "tools/list" request
    "tools/list": {
      jsonrpc: "2.0",
      result: {
        tools: [
          {
            name: "create_and_send_packet",
            description: "Creates a bail bond document packet and sends it for signing via SignNow. Supports both email mode (remote signing) and kiosk mode (in-office iPad signing). Requires defendant information and optional indemnitor details.",
            inputSchema: {
              type: "object",
              properties: {
                defendant_first_name: { type: "string", description: "Defendant's first name" },
                defendant_last_name: { type: "string", description: "Defendant's last name" },
                defendant_dob: { type: "string", description: "Defendant's date of birth (YYYY-MM-DD or MM/DD/YYYY)" },
                defendant_booking_number: { type: "string", description: "Booking number from arrest record" },
                defendant_email: { type: "string", description: "Defendant's email address (optional for kiosk mode)" },
                defendant_phone: { type: "string", description: "Defendant's phone number" },
                indemnitor_emails: { 
                  type: "array", 
                  items: { type: "string" },
                  description: "Array of indemnitor email addresses (optional for kiosk mode)" 
                },
                charges: {
                  type: "array",
                  items: { 
                    type: "object",
                    properties: {
                      description: { type: "string" },
                      bond_amount: { type: "string" },
                      case_number: { type: "string" }
                    }
                  },
                  description: "Array of charge objects with description, bond amount, case number"
                },
                bond_amount: { type: "string", description: "Total bond amount" },
                signing_method: {
                  type: "string",
                  enum: ["email", "kiosk"],
                  description: "Signing method: 'email' for remote or 'kiosk' for in-office"
                }
              },
              required: ["defendant_first_name", "defendant_last_name", "defendant_booking_number"]
            }
          },
          {
            name: "check_document_status",
            description: "Checks the signing status of a document in SignNow by document ID. Returns status, signed parties, and pending signers.",
            inputSchema: {
              type: "object",
              properties: {
                document_id: { type: "string", description: "SignNow document ID" }
              },
              required: ["document_id"]
            }
          },
          {
            name: "process_court_emails",
            description: "Processes new court date and forfeiture emails from shamrockbailoffice@gmail.com. Creates calendar events, logs to 'upcoming court dates' sheet tab, and posts notifications to Slack channels. Handles both court date notices and forfeiture notices.",
            inputSchema: {
              type: "object",
              properties: {
                lookback_days: { 
                  type: "number", 
                  description: "Number of days to look back for emails (default: 30)" 
                },
                process_historical: {
                  type: "boolean",
                  description: "If true, processes all emails from current year (default: false)"
                }
              }
            }
          },
          {
            name: "run_lead_scoring",
            description: "Runs lead scoring and qualification routing for county arrest records. Scores each record based on bond amount, charge severity, custody status, and other factors. Routes qualified leads (Warm/Hot) to the 'Qualified' tab. Released defendants never qualify (hard rule).",
            inputSchema: {
              type: "object",
              properties: {
                county: { 
                  type: "string",
                  enum: ["Lee", "Collier", "Hendry", "Charlotte", "Manatee", "DeSoto", "Sarasota", "Hillsborough", "Palm Beach", "all"],
                  description: "Specific county to score (optional, defaults to all counties)" 
                }
              }
            }
          },
          {
            name: "get_case_details",
            description: "Retrieves detailed information about a specific case from Google Sheets by booking number. Searches across all county tabs if county not specified.",
            inputSchema: {
              type: "object",
              properties: {
                booking_number: { type: "string", description: "Booking number to search for" },
                county: { type: "string", description: "County name (optional, searches all if not specified)" }
              },
              required: ["booking_number"]
            }
          },
          {
            name: "notify_slack",
            description: "Sends a notification message to a specified Slack channel. Supports court-dates, forfeitures, new-cases, and general channels.",
            inputSchema: {
              type: "object",
              properties: {
                channel: { 
                  type: "string", 
                  enum: ["court-dates", "forfeitures", "new-cases", "general"],
                  description: "Slack channel to post to" 
                },
                message: { type: "string", description: "Message content" },
                defendant_name: { type: "string", description: "Defendant name (optional, adds context)" },
                case_number: { type: "string", description: "Case number (optional, adds context)" },
                court_date: { type: "string", description: "Court date (optional, for court date notifications)" }
              },
              required: ["channel", "message"]
            }
          },
          {
            name: "run_county_scraper",
            description: "Runs the arrest record scraper for a specific county. Collects new booking records and saves to the county's Google Sheets tab.",
            inputSchema: {
              type: "object",
              properties: {
                county: { 
                  type: "string", 
                  enum: ["lee", "collier", "charlotte", "hendry", "sarasota", "desoto", "manatee"],
                  description: "County to scrape (lowercase)" 
                }
              },
              required: ["county"]
            }
          },
          {
            name: "get_dashboard_stats",
            description: "Retrieves current dashboard statistics including total cases, SignNow launches, premium generated, pending signatures, completed bonds, and active forfeitures.",
            inputSchema: {
              type: "object",
              properties: {
                date_range: { 
                  type: "string", 
                  enum: ["today", "week", "month", "all"],
                  description: "Time range for statistics (default: all)" 
                }
              }
            }
          },
          {
            name: "send_to_dashboard",
            description: "Sends a specific case from Google Sheets to the Dashboard.html form for manual review and paperwork generation. Pre-fills all defendant and charge information.",
            inputSchema: {
              type: "object",
              properties: {
                booking_number: { type: "string", description: "Booking number of the case to send" },
                county: { type: "string", description: "County name (optional)" }
              },
              required: ["booking_number"]
            }
          },
          {
            name: "update_custody_status",
            description: "Updates the in-custody status for all records in a specific county tab by checking current booking system data.",
            inputSchema: {
              type: "object",
              properties: {
                county: { 
                  type: "string",
                  description: "County to update (e.g., 'Lee', 'Collier')" 
                }
              },
              required: ["county"]
            }
          }
        ]
      }
    }
  };
}

/**
 * Map MCP tool names to actual GAS functions
 * This object tells MCPApp which function to call for each tool
 */
function getMCPFunctions_() {
  return {
    create_and_send_packet: createAndSendPacket_MCP,
    check_document_status: checkDocumentStatus_MCP,
    process_court_emails: processCourtEmails_MCP,
    run_lead_scoring: runLeadScoring_MCP,
    get_case_details: getCaseDetails_MCP,
    notify_slack: notifySlack_MCP,
    run_county_scraper: runCountyScraper_MCP,
    get_dashboard_stats: getDashboardStats_MCP,
    send_to_dashboard: sendToDashboard_MCP,
    update_custody_status: updateCustodyStatus_MCP
  };
}

// ============================================================================
// COMPONENT 2: MCP TOOL IMPLEMENTATIONS
// ============================================================================

/**
 * Creates and sends a bail bond packet via SignNow
 */
function createAndSendPacket_MCP(params) {
  try {
    Logger.log('MCP: create_and_send_packet called with params: ' + JSON.stringify(params));
    
    // Build form data object compatible with existing SignNow functions
    const formData = {
      defendantFirstName: params.defendant_first_name || '',
      defendantLastName: params.defendant_last_name || '',
      defendantDOB: params.defendant_dob || '',
      defendantBookingNumber: params.defendant_booking_number || '',
      defendantEmail: params.defendant_email || '',
      defendantPhone: params.defendant_phone || '',
      indemnitorEmails: params.indemnitor_emails || [],
      charges: params.charges || [],
      bondAmount: params.bond_amount || '',
      signingMethod: params.signing_method || 'email'
    };
    
    // Call existing SignNow integration function
    // This function should exist in SignNowAPI.gs or SignNow_Integration_Complete.gs
    const result = createAndSendSignNowPacket(formData);
    
    return {
      success: true,
      message: "Packet created and sent successfully",
      document_id: result.documentId || '',
      signing_links: result.signingLinks || [],
      receipt_number: result.receiptNumber || '',
      defendant_name: params.defendant_first_name + ' ' + params.defendant_last_name
    };
    
  } catch (error) {
    Logger.log('MCP Error in create_and_send_packet: ' + error.toString());
    return {
      success: false,
      error: error.toString(),
      error_details: error.stack || ''
    };
  }
}

/**
 * Checks SignNow document status
 */
function checkDocumentStatus_MCP(params) {
  try {
    Logger.log('MCP: check_document_status called for document: ' + params.document_id);
    
    // Call existing status check function
    const status = checkSignNowDocumentStatus(params.document_id);
    
    return {
      success: true,
      document_id: params.document_id,
      status: status.status || 'unknown',
      signed_by: status.signedBy || [],
      pending_signers: status.pendingSigners || [],
      completed_date: status.completedDate || null,
      last_updated: new Date().toISOString()
    };
    
  } catch (error) {
    Logger.log('MCP Error in check_document_status: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Processes court emails
 */
function processCourtEmails_MCP(params) {
  try {
    const lookbackDays = params.lookback_days || 30;
    const processHistorical = params.process_historical || false;
    
    Logger.log('MCP: process_court_emails called with lookback: ' + lookbackDays + ', historical: ' + processHistorical);
    
    let result;
    if (processHistorical) {
      // Call historical processing function from CourtEmailProcessor.gs
      result = processHistoricalEmails();
    } else {
      // Call regular processing function
      result = processCourtEmails(lookbackDays);
    }
    
    return {
      success: true,
      emails_processed: result.emailsProcessed || 0,
      court_dates_found: result.courtDatesFound || 0,
      forfeitures_found: result.forfeituresFound || 0,
      calendar_events_created: result.calendarEventsCreated || 0,
      slack_notifications_sent: result.slackNotificationsSent || 0,
      processing_time: result.processingTime || 'N/A'
    };
    
  } catch (error) {
    Logger.log('MCP Error in process_court_emails: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Runs lead scoring system
 */
function runLeadScoring_MCP(params) {
  try {
    const county = params.county || 'all';
    
    Logger.log('MCP: run_lead_scoring called for county: ' + county);
    
    let result;
    if (county === 'all' || !county) {
      // Score all counties
      result = scoreAndRouteAllSheets();
    } else {
      // Score specific county
      result = scoreCountySheet(county);
    }
    
    return {
      success: true,
      county: county,
      records_scored: result.recordsScored || 0,
      qualified_leads: result.qualifiedLeads || 0,
      hot_leads: result.hotLeads || 0,
      warm_leads: result.warmLeads || 0,
      cold_leads: result.coldLeads || 0,
      disqualified: result.disqualified || 0
    };
    
  } catch (error) {
    Logger.log('MCP Error in run_lead_scoring: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Retrieves case details by booking number
 */
function getCaseDetails_MCP(params) {
  try {
    const bookingNumber = params.booking_number;
    const county = params.county || null;
    
    Logger.log('MCP: get_case_details called for booking: ' + bookingNumber + ', county: ' + county);
    
    // Search for case in Google Sheets
    const caseData = searchCaseByBookingNumber(bookingNumber, county);
    
    if (!caseData) {
      return {
        success: false,
        error: "Case not found",
        booking_number: bookingNumber
      };
    }
    
    return {
      success: true,
      case: caseData
    };
    
  } catch (error) {
    Logger.log('MCP Error in get_case_details: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Sends notification to Slack
 */
function notifySlack_MCP(params) {
  try {
    const channel = params.channel;
    const message = params.message;
    
    Logger.log('MCP: notify_slack called for channel: ' + channel);
    
    // Get webhook URL for channel
    const webhookUrl = getSlackWebhookForChannel(channel);
    
    if (!webhookUrl) {
      return {
        success: false,
        error: "Slack webhook not configured for channel: " + channel
      };
    }
    
    // Build Slack message payload
    const payload = {
      text: message,
      blocks: []
    };
    
    // Add context if provided
    if (params.defendant_name || params.case_number || params.court_date) {
      const contextElements = [];
      if (params.defendant_name) contextElements.push("*Defendant:* " + params.defendant_name);
      if (params.case_number) contextElements.push("*Case:* " + params.case_number);
      if (params.court_date) contextElements.push("*Date:* " + params.court_date);
      
      payload.blocks.push({
        type: "section",
        text: {
          type: "mrkdwn",
          text: message
        }
      });
      
      payload.blocks.push({
        type: "context",
        elements: [{
          type: "mrkdwn",
          text: contextElements.join(" • ")
        }]
      });
    }
    
    // Send to Slack
    const result = postToSlack(webhookUrl, payload);
    
    return {
      success: true,
      message: "Slack notification sent",
      channel: channel
    };
    
  } catch (error) {
    Logger.log('MCP Error in notify_slack: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Runs county scraper
 */
function runCountyScraper_MCP(params) {
  try {
    const county = params.county.toLowerCase();
    
    Logger.log('MCP: run_county_scraper called for county: ' + county);
    
    let result;
    switch(county) {
      case 'lee':
        result = runLeeScraper();
        break;
      case 'collier':
        result = runCollierScraper();
        break;
      // Add other counties as they're implemented
      default:
        return {
          success: false,
          error: "Scraper not implemented for county: " + county
        };
    }
    
    return {
      success: true,
      county: county,
      records_found: result.recordsFound || 0,
      new_records: result.newRecords || 0,
      updated_records: result.updatedRecords || 0,
      scrape_time: result.scrapeTime || 'N/A'
    };
    
  } catch (error) {
    Logger.log('MCP Error in run_county_scraper: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Gets dashboard statistics
 */
function getDashboardStats_MCP(params) {
  try {
    const dateRange = params.date_range || 'all';
    
    Logger.log('MCP: get_dashboard_stats called for range: ' + dateRange);
    
    // Calculate statistics based on date range
    const stats = calculateDashboardStatistics(dateRange);
    
    return {
      success: true,
      date_range: dateRange,
      total_cases: stats.totalCases || 0,
      signnow_launches: stats.signnowLaunches || 0,
      total_premium: stats.totalPremium || 0,
      pending_signatures: stats.pendingSignatures || 0,
      completed_bonds: stats.completedBonds || 0,
      active_forfeitures: stats.activeForfeitures || 0,
      generated_at: new Date().toISOString()
    };
    
  } catch (error) {
    Logger.log('MCP Error in get_dashboard_stats: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Sends case to Dashboard.html for manual review
 */
function sendToDashboard_MCP(params) {
  try {
    const bookingNumber = params.booking_number;
    const county = params.county || null;
    
    Logger.log('MCP: send_to_dashboard called for booking: ' + bookingNumber);
    
    // Get case details
    const caseData = searchCaseByBookingNumber(bookingNumber, county);
    
    if (!caseData) {
      return {
        success: false,
        error: "Case not found"
      };
    }
    
    // Store in Script Properties for Dashboard.html to retrieve
    const formData = mapSheetDataToForm_(caseData);
    PropertiesService.getScriptProperties().setProperty('FORM_PREFILL_DATA', JSON.stringify(formData));
    
    // Get Dashboard URL
    const dashboardUrl = ScriptApp.getService().getUrl() + '?prefill=true';
    
    return {
      success: true,
      message: "Case data sent to Dashboard",
      dashboard_url: dashboardUrl,
      defendant_name: caseData.Full_Name || 'Unknown'
    };
    
  } catch (error) {
    Logger.log('MCP Error in send_to_dashboard: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

/**
 * Updates custody status for a county
 */
function updateCustodyStatus_MCP(params) {
  try {
    const county = params.county;
    
    Logger.log('MCP: update_custody_status called for county: ' + county);
    
    // Call existing custody status update function
    const result = updateInCustodyStatusForCounty(county);
    
    return {
      success: true,
      county: county,
      records_checked: result.recordsChecked || 0,
      status_changes: result.statusChanges || 0,
      still_in_custody: result.stillInCustody || 0,
      released: result.released || 0
    };
    
  } catch (error) {
    Logger.log('MCP Error in update_custody_status: ' + error.toString());
    return {
      success: false,
      error: error.toString()
    };
  }
}

// ============================================================================
// HELPER FUNCTIONS (to be implemented or linked to existing functions)
// ============================================================================

/**
 * Note: The following functions are called by the MCP tool implementations above.
 * They should either exist in your other GAS files or need to be created.
 * 
 * Expected functions:
 * - createAndSendSignNowPacket(formData)
 * - checkSignNowDocumentStatus(documentId)
 * - processCourtEmails(lookbackDays)
 * - processHistoricalEmails()
 * - scoreAndRouteAllSheets()
 * - scoreCountySheet(county)
 * - searchCaseByBookingNumber(bookingNumber, county)
 * - getSlackWebhookForChannel(channel)
 * - postToSlack(webhookUrl, payload)
 * - runLeeScraper()
 * - runCollierScraper()
 * - calculateDashboardStatistics(dateRange)
 * - mapSheetDataToForm_(caseData)
 * - updateInCustodyStatusForCounty(county)
 */
