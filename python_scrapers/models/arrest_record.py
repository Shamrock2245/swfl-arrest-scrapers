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
    Universal arrest record model with 39 fields.
    Matches the project's canonical data schema v3.0.
    """
    # === Master Schema (39 Columns) ===
    Scrape_Timestamp: str = ""   # 1. When record was scraped (ISO format)
    County: str = ""             # 2. Source county
    Booking_Number: str = ""     # 3. Primary Key
    Person_ID: str = ""          # 4. County-specific person ID
    Full_Name: str = ""          # 5. Full name
    First_Name: str = ""         # 6. First name
    Middle_Name: str = ""        # 7. Middle name
    Last_Name: str = ""          # 8. Last name
    DOB: str = ""                # 9. Date of birth
    Arrest_Date: str = ""        # 10. Date of arrest
    Arrest_Time: str = ""        # 11. Time of arrest
    Booking_Date: str = ""       # 12. Date booked
    Booking_Time: str = ""       # 13. Time booked
    Status: str = ""             # 14. Current status
    Facility: str = ""           # 15. Facility name
    Agency: str = ""             # 16. Arresting agency
    Race: str = ""               # 17. Race
    Sex: str = ""                # 18. Sex (M/F)
    Height: str = ""             # 19. Height
    Weight: str = ""             # 20. Weight
    Address: str = ""            # 21. Street address
    City: str = ""               # 22. City
    State: str = "FL"            # 23. State
    ZIP: str = ""                # 24. ZIP code
    Mugshot_URL: str = ""        # 25. URL to mugshot image
    Charges: str = ""            # 26. Pipe | separated charges
    Bond_Amount: str = "0"       # 27. Numeric bond amount
    Bond_Paid: str = "NO"        # 28. YES/NO
    Bond_Type: str = ""          # 29. CASH, SURETY, etc.
    Court_Type: str = ""         # 30. Felony, Misdemeanor, etc.
    Case_Number: str = ""        # 31. Court case number
    Court_Date: str = ""         # 32. Court date
    Court_Time: str = ""         # 33. Court time
    Court_Location: str = ""     # 34. Courthouse location
    Detail_URL: str = ""         # 35. Original source URL
    Lead_Score: int = 0          # 36. Calculated score
    Lead_Status: str = ""        # 37. Hot, Warm, Cold, Disqualified
    LastChecked: str = ""        # 38. Last verification time
    LastCheckedMode: str = ""    # 39. INITIAL, UPDATE, MANUAL

    # === INTERNAL METADATA (not part of 39-column output) ===
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
        """Returns the 39 fields in canonical order."""
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
            self.Arrest_Date,
            self.Arrest_Time,
            self.Booking_Date,
            self.Booking_Time,
            self.Status,
            self.Facility,
            self.Agency,
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
            self.LastChecked,
            self.LastCheckedMode
        ]

    @classmethod
    def get_header_row(cls) -> list:
        """Returns the canonical 39-column header row."""
        return [
            "Scrape_Timestamp", "County", "Booking_Number", "Person_ID", "Full_Name",
            "First_Name", "Middle_Name", "Last_Name", "DOB", "Arrest_Date", "Arrest_Time",
            "Booking_Date", "Booking_Time", "Status", "Facility", "Agency",
            "Race", "Sex", "Height", "Weight", "Address", "City", "State", "ZIP",
            "Mugshot_URL", "Charges", "Bond_Amount", "Bond_Paid", "Bond_Type",
            "Court_Type", "Case_Number", "Court_Date", "Court_Time", "Court_Location",
            "Detail_URL", "Lead_Score", "Lead_Status", "LastChecked", "LastCheckedMode"
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
SCHEMA_FIELD_COUNT = 39

class FieldIndex:
    """Constants for field positions (0-indexed)."""
    SCRAPE_TIMESTAMP = 0
    COUNTY = 1
    BOOKING_NUMBER = 2
    PERSON_ID = 3
    FULL_NAME = 4
    FIRST_NAME = 5
    DOB = 8
    ARREST_DATE = 9
    BOOKING_DATE = 11
    STATUS = 13
    AGENCY = 15
    MUGSHOT_URL = 24
    CHARGES = 25
    BOND_AMOUNT = 26
    CASE_NUMBER = 30
    LEAD_SCORE = 35
    LEAD_STATUS = 36
