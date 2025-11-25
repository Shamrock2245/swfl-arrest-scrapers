"""
ArrestRecord Model - Extended 34-Column Universal Schema

This module defines the canonical ArrestRecord model with integrated lead scoring.
Extends the original 32-column schema with Lead_Score and Lead_Status fields.

Author: SWFL Arrest Scrapers Team
Date: November 24, 2025
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json


@dataclass
class ArrestRecord:
    """
    Universal arrest record model with 34 fields including lead scoring.
    
    This model represents a standardized arrest record from any SWFL county,
    normalized to a common schema with integrated lead qualification scoring.
    
    Fields 1-32: Original universal schema
    Fields 33-34: Lead scoring extensions
    """
    
    # === IDENTIFICATION (Fields 1-4) ===
    Booking_Number: str = ""  # Primary identifier
    Full_Name: str = ""  # Last, First format
    First_Name: str = ""
    Last_Name: str = ""
    
    # === DEMOGRAPHICS (Fields 5-7) ===
    DOB: str = ""  # Date of birth (YYYY-MM-DD or MM/DD/YYYY)
    Sex: str = ""  # M, F, or other
    Race: str = ""  # Standardized race/ethnicity
    
    # === ARREST DETAILS (Fields 8-12) ===
    Arrest_Date: str = ""  # Date of arrest (YYYY-MM-DD)
    Arrest_Time: str = ""  # Time of arrest (HH:MM or HH:MM:SS)
    Booking_Date: str = ""  # Date booked into facility
    Booking_Time: str = ""  # Time booked
    Agency: str = ""  # Arresting agency name
    
    # === ADDRESS (Fields 13-17) ===
    Address: str = ""  # Street address
    City: str = ""
    State: str = "FL"  # Default to Florida
    Zipcode: str = ""
    
    # === CHARGES (Fields 18-24) ===
    Charges: str = ""  # Raw charges text (all charges concatenated)
    Charge_1: str = ""  # Primary charge description
    Charge_1_Statute: str = ""  # Statute number for charge 1
    Charge_1_Bond: str = ""  # Bond amount for charge 1
    Charge_2: str = ""  # Secondary charge (if any)
    Charge_2_Statute: str = ""
    Charge_2_Bond: str = ""
    
    # === BOND & COURT (Fields 25-28) ===
    Bond_Amount: str = ""  # Total bond amount (may include $ and commas)
    Bond_Type: str = ""  # CASH, SURETY, ROR, NO BOND, etc.
    Status: str = ""  # IN CUSTODY, RELEASED, etc.
    Court_Date: str = ""  # Next court appearance date
    
    # === CASE & IMAGES (Fields 29-30) ===
    Case_Number: str = ""  # Court case number
    Mugshot_URL: str = ""  # URL to mugshot image
    
    # === METADATA (Fields 31-32) ===
    County: str = ""  # Source county (Lee, Collier, etc.)
    Court_Location: str = ""  # Court location/jurisdiction
    
    # === LEAD SCORING (Fields 33-34) - NEW ===
    Lead_Score: int = 0  # Calculated lead qualification score
    Lead_Status: str = "Cold"  # Hot, Warm, Cold, or Disqualified
    
    # === INTERNAL METADATA (not part of 34-column output) ===
    ingested_at: Optional[datetime] = None  # When record was scraped
    source_url: Optional[str] = None  # Original source URL
    extra_data: Dict[str, Any] = field(default_factory=dict)  # Additional fields
    
    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Set ingestion timestamp if not provided
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow()
        
        # Normalize state to uppercase
        if self.State:
            self.State = self.State.upper()
        
        # Normalize sex to single character
        if self.Sex:
            self.Sex = self.Sex.upper()[:1]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert record to dictionary.
        
        Returns:
            Dictionary representation of the arrest record
        """
        return asdict(self)
    
    def to_sheet_row(self) -> list:
        """
        Convert record to a list suitable for Google Sheets row.
        Returns the 34 fields in the canonical order.
        
        Returns:
            List of 34 values in schema order
        """
        return [
            self.Booking_Number,
            self.Full_Name,
            self.First_Name,
            self.Last_Name,
            self.DOB,
            self.Sex,
            self.Race,
            self.Arrest_Date,
            self.Arrest_Time,
            self.Booking_Date,
            self.Booking_Time,
            self.Agency,
            self.Address,
            self.City,
            self.State,
            self.Zipcode,
            self.Charges,
            self.Charge_1,
            self.Charge_1_Statute,
            self.Charge_1_Bond,
            self.Charge_2,
            self.Charge_2_Statute,
            self.Charge_2_Bond,
            self.Bond_Amount,
            self.Bond_Type,
            self.Status,
            self.Court_Date,
            self.Case_Number,
            self.Mugshot_URL,
            self.County,
            self.Court_Location,
            self.Lead_Score,
            self.Lead_Status,
        ]
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert record to JSON string.
        
        Args:
            indent: Number of spaces for indentation (default: 2)
        
        Returns:
            JSON string representation
        """
        data = self.to_dict()
        # Convert datetime to ISO string
        if data.get('ingested_at'):
            data['ingested_at'] = data['ingested_at'].isoformat()
        return json.dumps(data, indent=indent, default=str)
    
    @classmethod
    def get_header_row(cls) -> list:
        """
        Get the canonical 34-column header row for Google Sheets.
        
        Returns:
            List of 34 column names in schema order
        """
        return [
            "Booking_Number",
            "Full_Name",
            "First_Name",
            "Last_Name",
            "DOB",
            "Sex",
            "Race",
            "Arrest_Date",
            "Arrest_Time",
            "Booking_Date",
            "Booking_Time",
            "Agency",
            "Address",
            "City",
            "State",
            "Zipcode",
            "Charges",
            "Charge_1",
            "Charge_1_Statute",
            "Charge_1_Bond",
            "Charge_2",
            "Charge_2_Statute",
            "Charge_2_Bond",
            "Bond_Amount",
            "Bond_Type",
            "Status",
            "Court_Date",
            "Case_Number",
            "Mugshot_URL",
            "County",
            "Court_Location",
            "Lead_Score",
            "Lead_Status",
        ]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArrestRecord':
        """
        Create an ArrestRecord from a dictionary.
        
        Args:
            data: Dictionary with field names as keys
        
        Returns:
            New ArrestRecord instance
        """
        # Filter to only known fields
        valid_fields = {
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        }
        return cls(**valid_fields)
    
    def is_qualified(self, min_score: int = 70) -> bool:
        """
        Check if this arrest qualifies as a lead based on score.
        
        Args:
            min_score: Minimum score threshold (default: 70)
        
        Returns:
            True if Lead_Score >= min_score and Lead_Status is not "Disqualified"
        """
        return self.Lead_Score >= min_score and self.Lead_Status != "Disqualified"
    
    def get_dedup_key(self) -> str:
        """
        Get a unique key for deduplication.
        Uses County + Booking_Number as the dedup key.
        
        Returns:
            Deduplication key string
        """
        return f"{self.County}:{self.Booking_Number}"


# Schema metadata
SCHEMA_VERSION = "2.0"
SCHEMA_FIELD_COUNT = 34
ORIGINAL_FIELD_COUNT = 32
SCORING_FIELDS = ["Lead_Score", "Lead_Status"]

# Field position constants (0-indexed)
class FieldIndex:
    """Constants for field positions in the 34-column schema."""
    BOOKING_NUMBER = 0
    FULL_NAME = 1
    FIRST_NAME = 2
    LAST_NAME = 3
    DOB = 4
    SEX = 5
    RACE = 6
    ARREST_DATE = 7
    ARREST_TIME = 8
    BOOKING_DATE = 9
    BOOKING_TIME = 10
    AGENCY = 11
    ADDRESS = 12
    CITY = 13
    STATE = 14
    ZIPCODE = 15
    CHARGES = 16
    CHARGE_1 = 17
    CHARGE_1_STATUTE = 18
    CHARGE_1_BOND = 19
    CHARGE_2 = 20
    CHARGE_2_STATUTE = 21
    CHARGE_2_BOND = 22
    BOND_AMOUNT = 23
    BOND_TYPE = 24
    STATUS = 25
    COURT_DATE = 26
    CASE_NUMBER = 27
    MUGSHOT_URL = 28
    COUNTY = 29
    COURT_LOCATION = 30
    LEAD_SCORE = 31
    LEAD_STATUS = 32
