/**
 * ============================================================================
 * Schema.gs - CENTRAL SOURCE OF TRUTH
 * ============================================================================
 * Defines the canonical 34-column schema for Arrest Records and
 * the Operational Queue schema for the document pipeline.
 *
 * PREVENTS DRIFT between Scrapers, Scorer, and Router.
 */

var Schema = (function() {

  // The 34 Canonical Columns (Do NOT change order)
  const ARREST_RECORD_COLUMNS = [
    "Booking_Number", "Full_Name", "First_Name", "Last_Name", "DOB", "Sex", "Race",
    "Arrest_Date", "Arrest_Time", "Booking_Date", "Booking_Time", "Agency",
    "Address", "City", "State", "Zipcode", "Charges", "Charge_1", "Charge_1_Statute",
    "Charge_1_Bond", "Charge_2", "Charge_2_Statute", "Charge_2_Bond", "Bond_Amount",
    "Bond_Type", "Status", "Court_Date", "Case_Number", "Mugshot_URL", "County",
    "Court_Location", "Detail_URL", "Lead_Score", "Lead_Status"
  ];

  // Columns for the "Qualified_Schema_Queue" (Arrest Record + Meta)
  const QUEUE_META_COLUMNS = [
    'router_dedupe_key',
    'router_source_tab',
    'router_synced_at',
    'signnow_status',            // PENDING | SENT | FAILED
    'signnow_last_attempt_at',
    'signnow_attempt_count',
    'signnow_error',
    'signnow_document_id'
  ];

  return {
    VERSION: "3.2",
    COLUMNS: ARREST_RECORD_COLUMNS,
    QUEUE_META: QUEUE_META_COLUMNS,
    TOTAL_COLUMNS: ARREST_RECORD_COLUMNS.length,
    
    /**
     * Helper to get a map of Header Name -> Index (0-based)
     */
    getMap: function() {
      const map = {};
      ARREST_RECORD_COLUMNS.forEach((h, i) => { map[h] = i; });
      return map;
    }
  };

})();
