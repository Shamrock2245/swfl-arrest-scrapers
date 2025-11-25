"""
Lead Scoring Module

Implements the lead qualification scoring logic for arrest records.
Ported from the original Apps Script LeadScoring.js implementation.

Scoring Rules:
- Bond amount: 500-50K (+30), 50K-100K (+20), >100K (+10), <500 (-10), 0 (-50)
- Bond type: CASH/SURETY (+25), NO BOND/HOLD (-50), ROR (-30)
- Status: IN CUSTODY (+20), RELEASED (-30)
- Data completeness: All required fields (+15), Missing data (-10)
- Disqualifying charges: capital/murder/federal (-100)

Lead Status Mapping:
- score < 0: Disqualified
- score >= 70: Hot
- score >= 40: Warm
- otherwise: Cold

Author: SWFL Arrest Scrapers Team
Date: November 24, 2025
"""

import re
from typing import Tuple, List
from ..models.arrest_record import ArrestRecord


class LeadScorer:
    """
    Lead scoring engine for arrest records.
    
    Calculates a qualification score and status based on multiple factors
    including bond amount, bond type, custody status, data completeness,
    and charge severity.
    """
    
    # Scoring thresholds
    BOND_TIER_1_MIN = 500
    BOND_TIER_1_MAX = 50000
    BOND_TIER_2_MAX = 100000
    
    # Score thresholds for status
    HOT_THRESHOLD = 70
    WARM_THRESHOLD = 40
    
    # Disqualifying charge keywords
    DISQUALIFYING_CHARGES = ['capital', 'murder', 'federal']
    
    def __init__(self):
        """Initialize the lead scorer."""
        self.debug_mode = False
        self.score_breakdown = []
    
    def score_arrest(self, record: ArrestRecord) -> Tuple[int, str]:
        """
        Calculate the lead score and status for an arrest record.
        
        This is the main scoring function that applies all scoring rules
        and returns the final score and status.
        
        Args:
            record: ArrestRecord instance to score
        
        Returns:
            Tuple of (score: int, status: str)
            - score: Integer score (can be negative)
            - status: "Hot", "Warm", "Cold", or "Disqualified"
        
        Example:
            >>> scorer = LeadScorer()
            >>> record = ArrestRecord(
            ...     Bond_Amount="$5,000",
            ...     Bond_Type="SURETY",
            ...     Status="IN CUSTODY",
            ...     Full_Name="DOE, JOHN",
            ...     Charges="DUI",
            ...     Court_Date="2025-12-01"
            ... )
            >>> score, status = scorer.score_arrest(record)
            >>> print(f"Score: {score}, Status: {status}")
            Score: 90, Status: Hot
        """
        self.score_breakdown = []
        total_score = 0
        
        # 1. Bond amount scoring
        bond_score, bond_reason = self._score_bond_amount(record.Bond_Amount)
        total_score += bond_score
        if bond_reason:
            self.score_breakdown.append(bond_reason)
        
        # 2. Bond type scoring
        bond_type_score, bond_type_reason = self._score_bond_type(record.Bond_Type)
        total_score += bond_type_score
        if bond_type_reason:
            self.score_breakdown.append(bond_type_reason)
        
        # 3. Status scoring
        status_score, status_reason = self._score_status(record.Status)
        total_score += status_score
        if status_reason:
            self.score_breakdown.append(status_reason)
        
        # 4. Data completeness scoring
        completeness_score, completeness_reason = self._score_data_completeness(record)
        total_score += completeness_score
        if completeness_reason:
            self.score_breakdown.append(completeness_reason)
        
        # 5. Disqualifying charges check (this can make score highly negative)
        disqual_score, disqual_reason = self._check_disqualifying_charges(record.Charges)
        total_score += disqual_score
        if disqual_reason:
            self.score_breakdown.append(disqual_reason)
        
        # 6. Determine lead status based on final score
        lead_status = self._determine_lead_status(total_score)
        
        return total_score, lead_status
    
    def _score_bond_amount(self, bond_amount: str) -> Tuple[int, str]:
        """
        Score based on bond amount.
        
        Rules:
        - 500 ≤ bond ≤ 50,000 → +30
        - 50,000 < bond ≤ 100,000 → +20
        - bond > 100,000 → +10
        - 0 < bond < 500 → -10
        - bond = 0 → -50
        
        Args:
            bond_amount: Bond amount string (may contain $, commas)
        
        Returns:
            Tuple of (score: int, reason: str)
        """
        # Extract numeric value from bond amount
        bond_value = self._parse_bond_amount(bond_amount)
        
        if bond_value is None:
            return 0, ""
        
        if bond_value == 0:
            return -50, "Bond amount: $0 (-50)"
        elif bond_value < self.BOND_TIER_1_MIN:
            return -10, f"Bond amount: ${bond_value:,.0f} < $500 (-10)"
        elif bond_value <= self.BOND_TIER_1_MAX:
            return 30, f"Bond amount: ${bond_value:,.0f} in $500-$50K range (+30)"
        elif bond_value <= self.BOND_TIER_2_MAX:
            return 20, f"Bond amount: ${bond_value:,.0f} in $50K-$100K range (+20)"
        else:
            return 10, f"Bond amount: ${bond_value:,.0f} > $100K (+10)"
    
    def _score_bond_type(self, bond_type: str) -> Tuple[int, str]:
        """
        Score based on bond type.
        
        Rules:
        - Contains CASH or SURETY → +25
        - Contains NO BOND or HOLD → -50
        - Contains ROR or R.O.R → -30
        
        Args:
            bond_type: Bond type string
        
        Returns:
            Tuple of (score: int, reason: str)
        """
        if not bond_type:
            return 0, ""
        
        bond_type_upper = bond_type.upper()
        
        # Check for NO BOND or HOLD (most restrictive)
        if 'NO BOND' in bond_type_upper or 'HOLD' in bond_type_upper:
            return -50, f"Bond type: {bond_type} (NO BOND/HOLD) (-50)"
        
        # Check for ROR (Release on Recognizance)
        if 'ROR' in bond_type_upper or 'R.O.R' in bond_type_upper:
            return -30, f"Bond type: {bond_type} (ROR) (-30)"
        
        # Check for CASH or SURETY (positive indicators)
        if 'CASH' in bond_type_upper or 'SURETY' in bond_type_upper:
            return 25, f"Bond type: {bond_type} (CASH/SURETY) (+25)"
        
        return 0, ""
    
    def _score_status(self, status: str) -> Tuple[int, str]:
        """
        Score based on custody status.
        
        Rules:
        - Contains IN CUSTODY or INCUSTODY → +20
        - Contains RELEASED → -30
        
        Args:
            status: Status string
        
        Returns:
            Tuple of (score: int, reason: str)
        """
        if not status:
            return 0, ""
        
        status_upper = status.upper()
        
        # Check for in custody (positive - person is still in jail)
        if 'IN CUSTODY' in status_upper or 'INCUSTODY' in status_upper:
            return 20, f"Status: {status} (IN CUSTODY) (+20)"
        
        # Check for released (negative - person already out)
        if 'RELEASED' in status_upper:
            return -30, f"Status: {status} (RELEASED) (-30)"
        
        return 0, ""
    
    def _score_data_completeness(self, record: ArrestRecord) -> Tuple[int, str]:
        """
        Score based on data completeness.
        
        Rules:
        - If Full_Name, Charges, Bond_Amount, and Court_Date are all non-empty: +15
        - Otherwise: -10
        
        Args:
            record: ArrestRecord instance
        
        Returns:
            Tuple of (score: int, reason: str)
        """
        required_fields = [
            ('Full_Name', record.Full_Name),
            ('Charges', record.Charges),
            ('Bond_Amount', record.Bond_Amount),
            ('Court_Date', record.Court_Date),
        ]
        
        missing_fields = [name for name, value in required_fields if not value or not value.strip()]
        
        if not missing_fields:
            return 15, "Complete data (all required fields present) (+15)"
        else:
            missing_str = ', '.join(missing_fields)
            return -10, f"Missing data: {missing_str} (-10)"
    
    def _check_disqualifying_charges(self, charges: str) -> Tuple[int, str]:
        """
        Check for disqualifying charges.
        
        Rules:
        - If charges contain 'capital', 'murder', or 'federal': -100
        
        Args:
            charges: Charges string
        
        Returns:
            Tuple of (score: int, reason: str)
        """
        if not charges:
            return 0, ""
        
        charges_lower = charges.lower()
        
        for keyword in self.DISQUALIFYING_CHARGES:
            if keyword in charges_lower:
                return -100, f"DISQUALIFIED: Severe charge ({keyword}) (-100)"
        
        return 0, ""
    
    def _determine_lead_status(self, score: int) -> str:
        """
        Determine lead status based on score.
        
        Rules:
        - score < 0 → "Disqualified"
        - score >= 70 → "Hot"
        - score >= 40 → "Warm"
        - otherwise → "Cold"
        
        Args:
            score: Total score
        
        Returns:
            Lead status string
        """
        if score < 0:
            return "Disqualified"
        elif score >= self.HOT_THRESHOLD:
            return "Hot"
        elif score >= self.WARM_THRESHOLD:
            return "Warm"
        else:
            return "Cold"
    
    def _parse_bond_amount(self, bond_amount: str) -> float:
        """
        Parse bond amount string to numeric value.
        
        Handles formats like:
        - "$5,000"
        - "5000"
        - "$5,000.00"
        - "No Bond" (returns None)
        
        Args:
            bond_amount: Bond amount string
        
        Returns:
            Numeric bond value or None if cannot parse
        """
        if not bond_amount or not bond_amount.strip():
            return None
        
        # Remove common non-numeric characters
        cleaned = bond_amount.strip().upper()
        
        # Check for special cases
        if any(term in cleaned for term in ['NO BOND', 'NONE', 'N/A', 'HOLD']):
            return 0.0
        
        # Remove $, commas, and whitespace
        cleaned = re.sub(r'[$,\s]', '', cleaned)
        
        # Try to convert to float
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def get_score_breakdown(self) -> List[str]:
        """
        Get the detailed breakdown of the last score calculation.
        
        Returns:
            List of scoring reason strings
        """
        return self.score_breakdown.copy()
    
    def score_and_update(self, record: ArrestRecord) -> ArrestRecord:
        """
        Score an arrest record and update its Lead_Score and Lead_Status fields.
        
        This is a convenience method that scores the record and updates it in place.
        
        Args:
            record: ArrestRecord instance to score and update
        
        Returns:
            The same ArrestRecord instance with updated scoring fields
        """
        score, status = self.score_arrest(record)
        record.Lead_Score = score
        record.Lead_Status = status
        return record


# Convenience function for quick scoring
def score_arrest(record: ArrestRecord) -> Tuple[int, str]:
    """
    Convenience function to score an arrest record.
    
    Args:
        record: ArrestRecord instance to score
    
    Returns:
        Tuple of (score: int, status: str)
    
    Example:
        >>> from python_scrapers.models.arrest_record import ArrestRecord
        >>> record = ArrestRecord(
        ...     Bond_Amount="$10,000",
        ...     Bond_Type="SURETY",
        ...     Status="IN CUSTODY",
        ...     Full_Name="SMITH, JANE",
        ...     Charges="Battery",
        ...     Court_Date="2025-12-15"
        ... )
        >>> score, status = score_arrest(record)
        >>> print(f"{score} - {status}")
        90 - Hot
    """
    scorer = LeadScorer()
    return scorer.score_arrest(record)


def score_and_update(record: ArrestRecord) -> ArrestRecord:
    """
    Convenience function to score and update an arrest record.
    
    Args:
        record: ArrestRecord instance to score and update
    
    Returns:
        The same ArrestRecord instance with updated scoring fields
    
    Example:
        >>> from python_scrapers.models.arrest_record import ArrestRecord
        >>> record = ArrestRecord(Bond_Amount="$5,000", Bond_Type="CASH")
        >>> record = score_and_update(record)
        >>> print(f"Score: {record.Lead_Score}, Status: {record.Lead_Status}")
        Score: 45, Status: Warm
    """
    scorer = LeadScorer()
    return scorer.score_and_update(record)
