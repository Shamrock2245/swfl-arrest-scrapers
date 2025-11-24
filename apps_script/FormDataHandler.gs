/**
 * FormDataHandler.gs
 * 
 * Handles data submission from the booking form (Form.html)
 * Saves booking data to a dedicated sheet
 */

/**
 * Save booking data from the form to the spreadsheet
 * 
 * @param {Object} formData - The form data object from Form.html
 * @return {Object} Result object with success status
 */
function saveBookingData(formData) {
  try {
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheetName = 'Manual_Bookings';
    var sheet = ss.getSheetByName(sheetName);
    
    // Create the sheet if it doesn't exist
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
      
      // Add headers
      var headers = [
        'Timestamp',
        'First Name',
        'Last Name',
        'Middle Name',
        'Date of Birth',
        'Booking Number',
        'Booking Date',
        'County',
        'Bond Amount',
        'Charges',
        'Phone',
        'Email',
        'Notes'
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
    
    // Prepare row data
    var rowData = [
      formData.timestamp || new Date(),
      formData.firstName || '',
      formData.lastName || '',
      formData.middleName || '',
      formData.dob || '',
      formData.bookingNumber || '',
      formData.bookingDate || '',
      formData.county || '',
      formData.bondAmount || '',
      formData.charges || '',
      formData.phone || '',
      formData.email || '',
      formData.notes || ''
    ];
    
    // Append the data
    sheet.appendRow(rowData);
    
    // Auto-resize columns
    sheet.autoResizeColumns(1, rowData.length);
    
    // Log the submission
    Logger.log('Booking data saved: ' + formData.bookingNumber + ' - ' + formData.firstName + ' ' + formData.lastName);
    
    return {
      success: true,
      message: 'Booking data saved successfully',
      bookingNumber: formData.bookingNumber
    };
    
  } catch (error) {
    Logger.log('Error saving booking data: ' + error.message);
    throw new Error('Failed to save booking data: ' + error.message);
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
