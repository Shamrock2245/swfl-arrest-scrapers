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
    Universal arrest record model with 34 fields.
    Matches the project's canonical data schema exactly.
    """
    # === Master Schema (34 Columns) ===
    Scrape_Timestamp: str = ""   # 1. When record was scraped (ISO format)
    County: str = ""             # 2. Source county (Lee, Collier, etc.)
    Booking_Number: str = ""     # 3. Primary Key
    Person_ID: str = ""          # 4. County-specific person ID
    Full_Name: str = ""          # 5. Full name
    First_Name: str = ""         # 6. First name
    Middle_Name: str = ""        # 7. Middle name
    Last_Name: str = ""          # 8. Last name
    DOB: str = ""                # 9. Date of birth
    Booking_Date: str = ""       # 10. Date booked
    Booking_Time: str = ""       # 11. Time booked
    Status: str = ""             # 12. Current status (In Custody, Released, etc.)
    Facility: str = ""           # 13. Facility name
    Race: str = ""               # 14. Race
    Sex: str = ""                # 15. Sex (M/F)
    Height: str = ""             # 16. Height
    Weight: str = ""             # 17. Weight
    Address: str = ""            # 18. Street address
    City: str = ""               # 19. City
    State: str = "FL"            # 20. State
    ZIP: str = ""                # 21. ZIP code
    Mugshot_URL: str = ""        # 22. URL to mugshot image
    Charges: str = ""            # 23. Pipe | separated charges
    Bond_Amount: str = "0"       # 24. Numeric bond amount
    Bond_Paid: str = "NO"        # 25. YES/NO
    Bond_Type: str = ""          # 26. CASH, SURETY, etc.
    Court_Type: str = ""         # 27. Felony, Misdemeanor, etc.
    Case_Number: str = ""        # 28. Court case number
    Court_Date: str = ""         # 29. Court date
    Court_Time: str = ""         # 30. Court time
    Court_Location: str = ""     # 31. Courthouse location
    Detail_URL: str = ""         # 32. Original source URL
    Lead_Score: int = 0          # 33. Calculated score
    Lead_Status: str = ""        # 34. Hot, Warm, Cold, Disqualified

    # === INTERNAL METADATA (not part of 34-column output) ===
    ingested_at: Optional[datetime] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Normalize data after initialization."""
        if not self.Scrape_Timestamp:
            self.Scrape_Timestamp = datetime.utcnow().isoformat()
        
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow()
        
        # Ensure Bond_Amount is numeric string
        if isinstance(self.Bond_Amount, (int, float)):
            self.Bond_Amount = str(self.Bond_Amount)
            
        # Normalize Sex
        if self.Sex:
            self.Sex = self.Sex.upper()[:1]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_sheet_row(self) -> list:
        """Returns the 34 fields in canonical order."""
        return [
            self.Scrape_Timestamp,
            self.County,
            self.Booking_Number,
            self.Person_ID,
            self.Full_Name,
            self.First_Name,
            self.Middle_Name,
            self.Last_Name,
            self.DOB,
            self.Booking_Date,
            self.Booking_Time,
            self.Status,
            self.Facility,
            self.Race,
            self.Sex,
            self.Height,
            self.Weight,
            self.Address,
            self.City,
            self.State,
            self.ZIP,
            self.Mugshot_URL,
            self.Charges,
            self.Bond_Amount,
            self.Bond_Paid,
            self.Bond_Type,
            self.Court_Type,
            self.Case_Number,
            self.Court_Date,
            self.Court_Time,
            self.Court_Location,
            self.Detail_URL,
            self.Lead_Score,
            self.Lead_Status,
        ]

    @classmethod
    def get_header_row(cls) -> list:
        """Returns the canonical 34-column header row."""
        return [
            "Scrape_Timestamp", "County", "Booking_Number", "Person_ID", "Full_Name",
            "First_Name", "Middle_Name", "Last_Name", "DOB", "Booking_Date",
            "Booking_Time", "Status", "Facility", "Race", "Sex", "Height", "Weight",
            "Address", "City", "State", "ZIP", "Mugshot_URL", "Charges",
            "Bond_Amount", "Bond_Paid", "Bond_Type", "Court_Type", "Case_Number",
            "Court_Date", "Court_Time", "Court_Location", "Detail_URL",
            "Lead_Score", "Lead_Status"
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArrestRecord':
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

    def is_qualified(self, min_score: int = 70) -> bool:
        return self.Lead_Score >= min_score and self.Lead_Status != "Disqualified"

    def get_dedup_key(self) -> str:
        return f"{self.County}:{self.Booking_Number}"

# Schema metadata
SCHEMA_VERSION = "3.0"
SCHEMA_FIELD_COUNT = 34

class FieldIndex:
    """Constants for field positions (0-indexed)."""
    SCRAPE_TIMESTAMP = 0
    COUNTY = 1
    BOOKING_NUMBER = 2
    PERSON_ID = 3
    FULL_NAME = 4
    FIRST_NAME = 5
    DOB = 8
    STATUS = 11
    MUGSHOT_URL = 21
    CHARGES = 22
    BOND_AMOUNT = 23
    CASE_NUMBER = 27
    LEAD_SCORE = 32
    LEAD_STATUS = 33
