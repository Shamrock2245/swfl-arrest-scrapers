"""
Google Sheets Writer Module

Handles writing arrest records to Google Sheets with the full 34-column schema.
Supports writing to county-specific tabs and the Qualified_Arrests sheet.

Features:
- 34-column output (32 original + Lead_Score + Lead_Status)
- Automatic header creation
- Deduplication based on County + Booking_Number
- Qualified arrests filtering (score >= 70)
- Batch writing for performance

Author: SWFL Arrest Scrapers Team
Date: November 24, 2025
"""

import os
import json
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import score_and_update


class SheetsWriter:
    """
    Google Sheets writer for arrest records.
    
    Writes ArrestRecord instances to Google Sheets with full 34-column schema
    including lead scoring fields.
    """
    
    # Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Default configuration
    DEFAULT_QUALIFIED_MIN_SCORE = 70
    QUALIFIED_SHEET_NAME = 'Qualified_Arrests'
    
    def __init__(
        self,
        spreadsheet_id: str,
        credentials_path: Optional[str] = None,
        qualified_min_score: int = DEFAULT_QUALIFIED_MIN_SCORE
    ):
        """
        Initialize the Sheets writer.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            credentials_path: Path to service account JSON credentials
            qualified_min_score: Minimum score for qualified arrests (default: 70)
        """
        self.spreadsheet_id = spreadsheet_id
        self.qualified_min_score = qualified_min_score
        
        # Initialize Google Sheets client
        # 1. Try direct JSON content from environment (supports raw JSON or Base64)
        if credentials_path is None:
            # Check for direct JSON content
            env_var = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') or os.getenv('GOOGLE_SA_KEY_JSON')
            
            if env_var:
                try:
                    content = env_var.strip()
                    # If it doesn't start with '{', assume Base64
                    if not content.startswith('{'):
                        decoded = base64.b64decode(content).decode('utf-8')
                        service_account_info = json.loads(decoded)
                    else:
                        service_account_info = json.loads(content)
                        
                    self.credentials = Credentials.from_service_account_info(
                        service_account_info,
                        scopes=self.SCOPES
                    )
                except Exception as e:
                    print(f"⚠️ Warning: Failed to parse Google Service Account env var: {e}")
                    # Fallthrough to file path check
            
        # 2. Fallback to file path
        if not hasattr(self, 'credentials'):
            if credentials_path is None:
                credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
            
            if not credentials_path:
                raise ValueError("Credentials must be provided via GOOGLE_SERVICE_ACCOUNT_JSON (env) or GOOGLE_SERVICE_ACCOUNT_KEY_PATH (file)")
            
            self.credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=self.SCOPES
            )
        
        self.client = gspread.authorize(self.credentials)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
    
    def write_records(
        self,
        records: List[ArrestRecord],
        county: str,
        auto_score: bool = True,
        deduplicate: bool = True
    ) -> Dict[str, Any]:
        """
        Write arrest records to the appropriate county sheet.
        
        Args:
            records: List of ArrestRecord instances
            county: County name (e.g., "Lee", "Collier")
            auto_score: Automatically score records if not already scored (default: True)
            deduplicate: Remove duplicates based on dedup key (default: True)
        
        Returns:
            Dictionary with write statistics:
            {
                'total_records': int,
                'new_records': int,
                'duplicates_skipped': int,
                'qualified_records': int,
                'sheet_name': str
            }
        """
        if not records:
            return {
                'total_records': 0,
                'new_records': 0,
                'duplicates_skipped': 0,
                'qualified_records': 0,
                'sheet_name': county
            }
        
        # Auto-score records if needed
        if auto_score:
            records = [score_and_update(r) if r.Lead_Score == 0 else r for r in records]
        
        # Get or create the county sheet
        sheet = self._get_or_create_sheet(county)
        
        # Ensure header row exists
        self._ensure_header_row(sheet)
        
        # Get existing records for deduplication
        existing_keys = set()
        if deduplicate:
            existing_keys = self._get_existing_dedup_keys(sheet)
        
        # Filter out duplicates
        new_records = []
        duplicates_skipped = 0
        
        for record in records:
            if deduplicate:
                dedup_key = record.get_dedup_key()
                if dedup_key in existing_keys:
                    duplicates_skipped += 1
                    continue
            new_records.append(record)
        
        # Write new records
        if new_records:
            rows = [record.to_sheet_row() for record in new_records]
            sheet.append_rows(rows, value_input_option='USER_ENTERED')
        
        # Count qualified records
        qualified_count = sum(1 for r in new_records if r.is_qualified(self.qualified_min_score))
        
        # Also write qualified records to Qualified_Arrests sheet
        if qualified_count > 0:
            qualified_records = [r for r in new_records if r.is_qualified(self.qualified_min_score)]
            self._write_qualified_records(qualified_records)
        
        return {
            'total_records': len(records),
            'new_records': len(new_records),
            'duplicates_skipped': duplicates_skipped,
            'qualified_records': qualified_count,
            'sheet_name': county
        }
    
    def _write_qualified_records(self, records: List[ArrestRecord]) -> None:
        """
        Write qualified records to the Qualified_Arrests sheet.
        
        Args:
            records: List of qualified ArrestRecord instances
        """
        if not records:
            return
        
        # Get or create Qualified_Arrests sheet
        sheet = self._get_or_create_sheet(self.QUALIFIED_SHEET_NAME)
        
        # Ensure header row
        self._ensure_header_row(sheet)
        
        # Get existing keys to avoid duplicates
        existing_keys = self._get_existing_dedup_keys(sheet)
        
        # Filter out duplicates
        new_records = []
        for record in records:
            dedup_key = record.get_dedup_key()
            if dedup_key not in existing_keys:
                new_records.append(record)
        
        # Write new qualified records
        if new_records:
            rows = [record.to_sheet_row() for record in new_records]
            sheet.append_rows(rows, value_input_option='USER_ENTERED')
    
    def _get_or_create_sheet(self, sheet_name: str) -> gspread.Worksheet:
        """
        Get an existing sheet or create it if it doesn't exist.
        
        Args:
            sheet_name: Name of the sheet
        
        Returns:
            Worksheet instance
        """
        try:
            return self.spreadsheet.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            # Create new sheet
            return self.spreadsheet.add_worksheet(
                title=sheet_name,
                rows=1000,
                cols=34
            )
    
    def _ensure_header_row(self, sheet: gspread.Worksheet) -> None:
        """
        Ensure the sheet has the correct 34-column header row.
        
        Args:
            sheet: Worksheet instance
        """
        # Check if sheet is empty or has wrong headers
        try:
            existing_headers = sheet.row_values(1)
            if existing_headers == ArrestRecord.get_header_row():
                return  # Headers are correct
        except:
            pass
        
        # Set the header row
        headers = ArrestRecord.get_header_row()
        sheet.update('A1:AH1', [headers], value_input_option='USER_ENTERED')
        
        # Format header row (bold, frozen)
        sheet.format('A1:AH1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.0, 'green': 0.66, 'blue': 0.42}
        })
        sheet.freeze(rows=1)
    
    def _get_existing_dedup_keys(self, sheet: gspread.Worksheet) -> set:
        """
        Get all existing deduplication keys from a sheet.
        
        Dedup key format: County:Booking_Number
        
        Args:
            sheet: Worksheet instance
        
        Returns:
            Set of dedup key strings
        """
        try:
            # Get all data
            all_values = sheet.get_all_values()
            
            if len(all_values) <= 1:
                return set()  # Only header or empty
            
            # Master Schema Indices:
            # County = Index 1
            # Booking_Number = Index 2
            dedup_keys = set()
            for row in all_values[1:]:  # Skip header
                if len(row) > 2:
                    county = row[1] if len(row) > 1 else ""
                    booking_number = row[2] if len(row) > 2 else ""
                    if booking_number and county:
                        dedup_keys.add(f"{county}:{booking_number}")
            
            return dedup_keys
        
        except Exception as e:
            print(f"Warning: Could not get existing dedup keys: {e}")
            return set()
    
    def log_ingestion(
        self,
        county: str,
        stats: Dict[str, Any],
        error: Optional[str] = None
    ) -> None:
        """
        Log an ingestion run to the Logs sheet.
        
        Args:
            county: County name
            stats: Statistics dictionary from write_records()
            error: Error message if ingestion failed (optional)
        """
        try:
            logs_sheet = self._get_or_create_sheet('Logs')
            
            # Ensure header row
            try:
                existing_headers = logs_sheet.row_values(1)
                if not existing_headers or existing_headers[0] != 'Timestamp':
                    logs_sheet.update('A1:H1', [[
                        'Timestamp',
                        'County',
                        'Total_Records',
                        'New_Records',
                        'Duplicates_Skipped',
                        'Qualified_Records',
                        'Status',
                        'Error'
                    ]], value_input_option='USER_ENTERED')
                    logs_sheet.format('A1:H1', {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.4, 'green': 0.5, 'blue': 0.9}
                    })
            except:
                pass
            
            # Add log entry
            timestamp = datetime.utcnow().isoformat()
            status = 'ERROR' if error else 'SUCCESS'
            
            log_row = [
                timestamp,
                county,
                stats.get('total_records', 0),
                stats.get('new_records', 0),
                stats.get('duplicates_skipped', 0),
                stats.get('qualified_records', 0),
                status,
                error or ''
            ]
            
            logs_sheet.append_row(log_row, value_input_option='USER_ENTERED')
        
        except Exception as e:
            print(f"Warning: Could not log ingestion: {e}")
    
    def get_qualified_records(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get qualified arrest records from the Qualified_Arrests sheet.
        
        Args:
            limit: Maximum number of records to return (optional)
        
        Returns:
            List of record dictionaries
        """
        try:
            sheet = self.spreadsheet.worksheet(self.QUALIFIED_SHEET_NAME)
            records = sheet.get_all_records()
            
            if limit:
                records = records[:limit]
            
            return records
        
        except gspread.WorksheetNotFound:
            return []
    
    def clear_sheet(self, sheet_name: str, keep_header: bool = True) -> None:
        """
        Clear all data from a sheet.
        
        Args:
            sheet_name: Name of the sheet to clear
            keep_header: Keep the header row (default: True)
        """
        try:
            sheet = self.spreadsheet.worksheet(sheet_name)
            
            if keep_header:
                # Clear everything except row 1
                sheet.batch_clear(['A2:AH10000'])
            else:
                # Clear everything
                sheet.clear()
        
        except gspread.WorksheetNotFound:
            print(f"Warning: Sheet '{sheet_name}' not found")


# Convenience function
def write_to_sheets(
    records: List[ArrestRecord],
    county: str,
    spreadsheet_id: str,
    credentials_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to write records to Google Sheets.
    
    Args:
        records: List of ArrestRecord instances
        county: County name
        spreadsheet_id: Google Sheets spreadsheet ID
        credentials_path: Path to service account credentials (optional)
    
    Returns:
        Statistics dictionary
    
    Example:
        >>> records = [ArrestRecord(...), ArrestRecord(...)]
        >>> stats = write_to_sheets(
        ...     records,
        ...     "Lee",
        ...     "121z5R6Hpqur54GNPC8L26ccfDPLHTJc3_LU6G7IV_0E"
        ... )
        >>> print(f"Wrote {stats['new_records']} new records")
    """
    writer = SheetsWriter(spreadsheet_id, credentials_path)
    return writer.write_records(records, county)
