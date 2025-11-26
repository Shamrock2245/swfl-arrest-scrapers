/**
 * FormDataHandler.gs
 * 
 * Handles data submission from the booking form (Form.html)
 * Saves booking data to a dedicated sheet
 * 
 * FIXED VERSION: Better error handling and validation
 */

/**
 * Save booking data from the form to the spreadsheet
 * 
 * @param {Object} formData - The form data object from Form.html
 * @return {Object} Result object with success status
 */
function saveBookingData(formData) {
  try {
    // Validate formData
    if (!formData || typeof formData !== 'object') {
      throw new Error('Invalid form data: formData is ' + typeof formData);
    }
    
    Logger.log('Received form data: ' + JSON.stringify(formData));
    
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = 'Manual_Bookings';
    var sheet = ss.getSheetByName(sheetName);
    
    // Create the sheet if it doesn't exist
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      
      // Add headers
      var headers = [
        'Timestamp',
        'Booking Number',
        'First Name',
        'Last Name',
        'Middle Name',
        'Date of Birth',
        'Sex',
        'Race',
        'Booking Date',
        'Arrest Date',
        'County',
        'Agency',
        'Address',
        'City',
        'State',
        'Zipcode',
        'Charges',
        'Charge 1',
        'Charge 1 Statute',
        'Charge 1 Bond',
        'Charge 2',
        'Charge 2 Statute',
        'Charge 2 Bond',
        'Bond Amount',
        'Bond Type',
        'Status',
        'Court Date',
        'Case Number',
        'Court Location',
        'Phone',
        'Email',
        'Notes',
        'Lead Score',
        'Lead Status'
      ];
      
      sheet.appendRow(headers);
      
      // Format header row
      var headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setBackground('#667eea');
      headerRange.setFontColor('#ffffff');
      headerRange.setFontWeight('bold');
      
      // Freeze header row
      sheet.setFrozenRows(1);
    }
    
    // Get current timestamp
    var timestamp = new Date();
    
    // Prepare row data - match the header order
    var rowData = [
      timestamp,
      formData.bookingNumber || formData.Booking_Number || '',
      formData.firstName || formData.First_Name || '',
      formData.lastName || formData.Last_Name || '',
      formData.middleName || formData.Middle_Name || '',
      formData.dob || formData.DOB || '',
      formData.sex || formData.Sex || '',
      formData.race || formData.Race || '',
      formData.bookingDate || formData.Booking_Date || '',
      formData.arrestDate || formData.Arrest_Date || '',
      formData.county || formData.County || '',
      formData.agency || formData.Agency || '',
      formData.address || formData.Address || '',
      formData.city || formData.City || '',
      formData.state || formData.State || 'FL',
      formData.zipcode || formData.Zipcode || '',
      formData.charges || formData.Charges || '',
      formData.charge1 || formData.Charge_1 || '',
      formData.charge1Statute || formData.Charge_1_Statute || '',
      formData.charge1Bond || formData.Charge_1_Bond || '',
      formData.charge2 || formData.Charge_2 || '',
      formData.charge2Statute || formData.Charge_2_Statute || '',
      formData.charge2Bond || formData.Charge_2_Bond || '',
      formData.bondAmount || formData.Bond_Amount || '',
      formData.bondType || formData.Bond_Type || '',
      formData.status || formData.Status || '',
      formData.courtDate || formData.Court_Date || '',
      formData.caseNumber || formData.Case_Number || '',
      formData.courtLocation || formData.Court_Location || '',
      formData.phone || '',
      formData.email || '',
      formData.notes || '',
      formData.leadScore || formData.Lead_Score || '',
      formData.leadStatus || formData.Lead_Status || ''
    ];
    
    // Append the data
    sheet.appendRow(rowData);
    
    // Auto-resize columns
    for (var i = 1; i <= rowData.length; i++) {
      sheet.autoResizeColumn(i);
    }
    
    // Log the submission
    var bookingNum = formData.bookingNumber || formData.Booking_Number || 'N/A';
    var firstName = formData.firstName || formData.First_Name || '';
    var lastName = formData.lastName || formData.Last_Name || '';
    
    Logger.log('Booking data saved: ' + bookingNum + ' - ' + firstName + ' ' + lastName);
    
    return {
      success: true,
      message: 'Booking data saved successfully',
      bookingNumber: bookingNum,
      timestamp: timestamp.toISOString()
    };
    
  } catch (error) {
    Logger.log('Error saving booking data: ' + error.message);
    Logger.log('Stack trace: ' + error.stack);
    
    return {
      success: false,
      message: 'Failed to save booking data: ' + error.message,
      error: error.toString()
    };
  }
}

/**
 * Web app entry point - handles GET and POST requests
 * This is called when the form is submitted via bookmarklet
 */
function doGet(e) {
  try {
    // If parameters are provided, it's from the bookmarklet
    if (e && e.parameter) {
      Logger.log('doGet called with parameters: ' + JSON.stringify(e.parameter));
      
      // Return the HTML form with pre-filled data
      var template = HtmlService.createTemplateFromFile('Form_Enhanced');
      template.params = e.parameter;
      
      return template.evaluate()
        .setTitle('Booking Form')
        .setWidth(900)
        .setHeight(700);
    }
    
    // No parameters - return empty form
    return HtmlService.createHtmlOutputFromFile('Form_Enhanced')
      .setTitle('Booking Form')
      .setWidth(900)
      .setHeight(700);
      
  } catch (error) {
    Logger.log('Error in doGet: ' + error.message);
    return HtmlService.createHtmlOutput('<h1>Error</h1><p>' + error.message + '</p>');
  }
}

/**
 * Get booking data by booking number
 * 
 * @param {string} bookingNumber - The booking number to search for
 * @return {Object} Booking data object or null if not found
 */
function getBookingByNumber(bookingNumber) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName('Manual_Bookings');
    
    if (!sheet) {
      return null;
    }
    
    var data = sheet.getDataRange().getValues();
    var headers = data[0];
    
    // Find the booking number column
    var bookingNumCol = headers.indexOf('Booking Number');
    
    if (bookingNumCol === -1) {
      return null;
    }
    
    // Search for the booking number
    for (var i = 1; i < data.length; i++) {
      if (data[i][bookingNumCol] === bookingNumber) {
        // Create object from row data
        var booking = {};
        for (var j = 0; j < headers.length; j++) {
          booking[headers[j]] = data[i][j];
        }
        return booking;
      }
    }
    
    return null;
    
  } catch (error) {
    Logger.log('Error getting booking data: ' + error.message);
    return null;
  }
}

/**
 * Delete a booking by booking number
 * 
 * @param {string} bookingNumber - The booking number to delete
 * @return {boolean} True if deleted, false otherwise
 */
function deleteBooking(bookingNumber) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getSheetByName('Manual_Bookings');
    
    if (!sheet) {
      return false;
    }
    
    var data = sheet.getDataRange().getValues();
    var headers = data[0];
    var bookingNumCol = headers.indexOf('Booking Number');
    
    if (bookingNumCol === -1) {
      return false;
    }
    
    // Find and delete the row
    for (var i = 1; i < data.length; i++) {
      if (data[i][bookingNumCol] === bookingNumber) {
        sheet.deleteRow(i + 1); // +1 because sheet rows are 1-indexed
        Logger.log('Deleted booking: ' + bookingNumber);
        return true;
      }
    }
    
    return false;
    
  } catch (error) {
    Logger.log('Error deleting booking: ' + error.message);
    return false;
  }
}
