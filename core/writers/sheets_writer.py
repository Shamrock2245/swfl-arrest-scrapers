"""
Google Sheets Writer — core/writers/sheets_writer.py

Writes arrest records to Google Sheets with:
- 39-column header in row 1 (auto-created if missing)
- NEW RECORDS INSERTED AT ROW 2 (newest first — today's arrests at top)
- Deduplication by County + Booking_Number
- Qualified_Arrests cross-posting for high-score leads
- Ingestion logging

Ported from python_scrapers/writers/sheets_writer.py with row-2 insert fix.
"""

import os
import json
import base64
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# 39-column canonical header (matches ArrestRecord.get_header_row())
HEADER_ROW = [
    "Scrape_Timestamp", "County", "Booking_Number", "Person_ID", "Full_Name",
    "First_Name", "Middle_Name", "Last_Name", "DOB", "Arrest_Date", "Arrest_Time",
    "Booking_Date", "Booking_Time", "Status", "Facility", "Agency",
    "Race", "Sex", "Height", "Weight", "Address", "City", "State", "ZIP",
    "Mugshot_URL", "Charges", "Bond_Amount", "Bond_Paid", "Bond_Type",
    "Court_Type", "Case_Number", "Court_Date", "Court_Time", "Court_Location",
    "Detail_URL", "Lead_Score", "Lead_Status", "LastChecked", "LastCheckedMode"
]

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]


def _build_credentials(credentials_path: Optional[str] = None) -> Credentials:
    """Build Google credentials from env var (JSON or Base64) or file path."""
    # 1. Try direct JSON content from environment
    env_var = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') or os.getenv('GOOGLE_SA_KEY_JSON')
    if env_var:
        content = env_var.strip()
        if not content.startswith('{'):
            content = base64.b64decode(content).decode('utf-8')
        info = json.loads(content)
        return Credentials.from_service_account_info(info, scopes=SCOPES)

    # 2. File path
    if credentials_path is None:
        credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
    if not credentials_path:
        raise ValueError(
            "Credentials required via GOOGLE_SERVICE_ACCOUNT_JSON (env), "
            "GOOGLE_SA_KEY_JSON (env), or GOOGLE_SERVICE_ACCOUNT_KEY_PATH (file path)"
        )
    return Credentials.from_service_account_file(credentials_path, scopes=SCOPES)


class SheetsWriter:
    """
    Writes arrest records to Google Sheets.

    Key behavior:
    - Header locked in row 1
    - New records INSERT at row 2 (pushing older records down)
    - Deduplication by County:Booking_Number composite key
    """

    QUALIFIED_SHEET = 'Qualified_Arrests'
    QUALIFIED_MIN_SCORE = 70

    def __init__(self, spreadsheet_id: str, credentials_path: Optional[str] = None):
        self.spreadsheet_id = spreadsheet_id
        creds = _build_credentials(credentials_path)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_records(
        self,
        records: List[Dict[str, Any]],
        county: str,
        deduplicate: bool = True
    ) -> Dict[str, Any]:
        """
        Write arrest record dicts to the county's sheet tab.

        Records are inserted at ROW 2 so newest arrests appear at top.

        Args:
            records: List of record dicts (keys matching HEADER_ROW)
            county: County name (used as sheet tab name)
            deduplicate: Skip records whose Booking_Number already exists

        Returns:
            Stats dict with new_records, duplicates_skipped, qualified_records
        """
        stats = {
            'total_records': len(records),
            'new_records': 0,
            'duplicates_skipped': 0,
            'qualified_records': 0,
            'updated_records': 0,
            'sheet_name': county
        }

        if not records:
            return stats

        sheet = self._get_or_create_sheet(county)
        self._ensure_header(sheet)

        # Get existing dedup keys
        existing_keys = set()
        if deduplicate:
            existing_keys = self._get_existing_keys(sheet)

        # Filter duplicates and build rows
        new_rows = []
        for record in records:
            booking = record.get('Booking_Number', '')
            rec_county = record.get('County', county)
            dedup_key = f"{rec_county}:{booking}"

            if deduplicate and dedup_key in existing_keys:
                stats['duplicates_skipped'] += 1
                continue

            row = self._record_to_row(record, county)
            new_rows.append(row)

            # Track qualified
            try:
                score = int(record.get('Lead_Score', 0))
                status = record.get('Lead_Status', '')
                if score >= self.QUALIFIED_MIN_SCORE and status != 'Disqualified':
                    stats['qualified_records'] += 1
            except (ValueError, TypeError):
                pass

        if not new_rows:
            return stats

        # INSERT at row 2 (newest first) — batch insert
        sheet.insert_rows(new_rows, row=2, value_input_option='USER_ENTERED')
        stats['new_records'] = len(new_rows)

        logger.info(
            f"Wrote {len(new_rows)} new records to '{county}' sheet "
            f"({stats['duplicates_skipped']} duplicates skipped)"
        )

        # Cross-post qualified records to Qualified_Arrests sheet
        qualified_rows = [
            r for r, rec in zip(new_rows, records)
            if int(rec.get('Lead_Score', 0)) >= self.QUALIFIED_MIN_SCORE
        ]
        if qualified_rows:
            self._write_qualified(qualified_rows)

        return stats

    def log_ingestion(
        self, county: str, stats: Dict[str, Any], error: Optional[str] = None
    ) -> None:
        """Log scraper run to the 'Logs' sheet tab."""
        try:
            sheet = self._get_or_create_sheet('Ingestion_Log')
            log_headers = [
                'Timestamp', 'County', 'Total_Records', 'New_Records',
                'Duplicates_Skipped', 'Qualified_Records', 'Status', 'Error'
            ]
            # Ensure header
            try:
                if sheet.row_values(1) != log_headers:
                    sheet.update('A1:H1', [log_headers], value_input_option='USER_ENTERED')
                    sheet.freeze(rows=1)
            except Exception:
                sheet.update('A1:H1', [log_headers], value_input_option='USER_ENTERED')

            log_row = [
                datetime.utcnow().isoformat(),
                county,
                stats.get('total_records', 0),
                stats.get('new_records', 0),
                stats.get('duplicates_skipped', 0),
                stats.get('qualified_records', 0),
                'ERROR' if error else 'SUCCESS',
                error or ''
            ]
            sheet.insert_rows([log_row], row=2, value_input_option='USER_ENTERED')
        except Exception as e:
            logger.warning(f"Could not log ingestion: {e}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_or_create_sheet(self, name: str) -> gspread.Worksheet:
        try:
            return self.spreadsheet.worksheet(name)
        except gspread.WorksheetNotFound:
            return self.spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADER_ROW))

    def _ensure_header(self, sheet: gspread.Worksheet) -> None:
        """Write header to row 1 if missing or wrong."""
        try:
            existing = sheet.row_values(1)
            if existing == HEADER_ROW:
                return
        except Exception:
            pass

        col_letter = chr(ord('A') + len(HEADER_ROW) - 1)  # 'AM' for 39 cols
        # For columns > Z, we need AA+ notation
        n = len(HEADER_ROW)
        if n <= 26:
            col_letter = chr(ord('A') + n - 1)
        else:
            col_letter = chr(ord('A') + (n - 1) // 26 - 1) + chr(ord('A') + (n - 1) % 26)

        sheet.update(f'A1:{col_letter}1', [HEADER_ROW], value_input_option='USER_ENTERED')
        sheet.format(f'A1:{col_letter}1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.0, 'green': 0.66, 'blue': 0.42}
        })
        sheet.freeze(rows=1)

    def _get_existing_keys(self, sheet: gspread.Worksheet) -> set:
        """Get County:Booking_Number composite keys from existing rows."""
        try:
            all_values = sheet.get_all_values()
            if len(all_values) <= 1:
                return set()

            # County = col index 1, Booking_Number = col index 2
            keys = set()
            for row in all_values[1:]:
                if len(row) > 2 and row[1] and row[2]:
                    keys.add(f"{row[1]}:{row[2]}")
            return keys
        except Exception as e:
            logger.warning(f"Could not read existing keys: {e}")
            return set()

    def _record_to_row(self, record: dict, county: str) -> list:
        """Convert a record dict to a 39-element list in header order."""
        row = []
        for col in HEADER_ROW:
            val = record.get(col, '')
            if val is None:
                val = ''
            row.append(str(val))
        # Ensure County is set
        if not row[1]:
            row[1] = county
        # Ensure Scrape_Timestamp is set
        if not row[0]:
            row[0] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        return row

    def _write_qualified(self, rows: list) -> None:
        """Cross-post qualified rows to the Qualified_Arrests sheet."""
        try:
            sheet = self._get_or_create_sheet(self.QUALIFIED_SHEET)
            self._ensure_header(sheet)
            existing_keys = self._get_existing_keys(sheet)

            new_rows = []
            for row in rows:
                key = f"{row[1]}:{row[2]}" if len(row) > 2 else ''
                if key and key not in existing_keys:
                    new_rows.append(row)

            if new_rows:
                sheet.insert_rows(new_rows, row=2, value_input_option='USER_ENTERED')
        except Exception as e:
            logger.warning(f"Could not write qualified records: {e}")


# ------------------------------------------------------------------
# Convenience function
# ------------------------------------------------------------------

def write_to_sheets(
    records: List[Dict[str, Any]],
    county: str,
    spreadsheet_id: Optional[str] = None,
    credentials_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    One-liner to write records to Google Sheets.

    Args:
        records: List of record dicts
        county: County name
        spreadsheet_id: Google Sheets ID (default from env GOOGLE_SHEETS_ID)
        credentials_path: Service account key path (default from env)

    Returns:
        Stats dict
    """
    if spreadsheet_id is None:
        spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
        if not spreadsheet_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable not set")

    writer = SheetsWriter(spreadsheet_id, credentials_path)
    return writer.write_records(records, county)
