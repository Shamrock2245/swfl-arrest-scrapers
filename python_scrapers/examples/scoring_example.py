"""
Lead Scoring Example

Demonstrates the lead scoring system with various example arrest records.

This script shows:
1. Creating ArrestRecord instances
2. Scoring them with the LeadScorer
3. Understanding the scoring breakdown
4. Different lead status outcomes

Author: SWFL Arrest Scrapers Team
Date: November 24, 2025
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from python_scrapers.models.arrest_record import ArrestRecord
from python_scrapers.scoring.lead_scorer import LeadScorer, score_and_update


def print_record_summary(record: ArrestRecord, scorer: LeadScorer = None):
    """Print a formatted summary of an arrest record with scoring details."""
    print(f"\n{'='*80}")
    print(f"ARREST RECORD: {record.Full_Name}")
    print(f"{'='*80}")
    print(f"Booking Number: {record.Booking_Number}")
    print(f"County: {record.County}")
    print(f"Bond Amount: {record.Bond_Amount}")
    print(f"Bond Type: {record.Bond_Type}")
    print(f"Status: {record.Status}")
    print(f"Charges: {record.Charges}")
    print(f"Court Date: {record.Court_Date}")
    print(f"\n{'-'*80}")
    print(f"LEAD SCORE: {record.Lead_Score}")
    print(f"LEAD STATUS: {record.Lead_Status}")
    print(f"{'-'*80}")
    
    if scorer:
        breakdown = scorer.get_score_breakdown()
        if breakdown:
            print("\nScoring Breakdown:")
            for reason in breakdown:
                print(f"  • {reason}")
    
    print(f"{'='*80}\n")


def main():
    """Run example scenarios."""
    
    print("\n" + "="*80)
    print("SWFL ARREST SCRAPERS - LEAD SCORING EXAMPLES")
    print("="*80)
    
    scorer = LeadScorer()
    
    # Example 1: HOT LEAD - Perfect scenario
    print("\n\n### EXAMPLE 1: HOT LEAD (High-value, in custody, complete data)")
    record1 = ArrestRecord(
        Booking_Number="2025-001234",
        Full_Name="SMITH, JOHN MICHAEL",
        First_Name="JOHN",
        Last_Name="SMITH",
        DOB="1985-06-15",
        Sex="M",
        Race="White",
        Arrest_Date="2025-11-24",
        Booking_Date="2025-11-24",
        County="Lee",
        Bond_Amount="$10,000",
        Bond_Type="SURETY",
        Status="IN CUSTODY",
        Charges="DUI with Property Damage",
        Court_Date="2025-12-15",
        Case_Number="2025-CF-001234"
    )
    
    score, status = scorer.score_arrest(record1)
    record1.Lead_Score = score
    record1.Lead_Status = status
    print_record_summary(record1, scorer)
    
    # Example 2: WARM LEAD - Medium bond, some data
    print("\n\n### EXAMPLE 2: WARM LEAD (Medium bond, cash bond)")
    record2 = ArrestRecord(
        Booking_Number="2025-001235",
        Full_Name="JOHNSON, SARAH ANN",
        First_Name="SARAH",
        Last_Name="JOHNSON",
        DOB="1992-03-22",
        County="Collier",
        Bond_Amount="$2,500",
        Bond_Type="CASH BOND",
        Status="IN CUSTODY",
        Charges="Petit Theft",
        Court_Date="2025-12-10"
    )
    
    score, status = scorer.score_arrest(record2)
    record2.Lead_Score = score
    record2.Lead_Status = status
    print_record_summary(record2, scorer)
    
    # Example 3: COLD LEAD - Low bond, released
    print("\n\n### EXAMPLE 3: COLD LEAD (Low bond, released, incomplete data)")
    record3 = ArrestRecord(
        Booking_Number="2025-001236",
        Full_Name="WILLIAMS, ROBERT",
        County="Charlotte",
        Bond_Amount="$250",
        Bond_Type="SURETY",
        Status="RELEASED",
        Charges="Trespassing"
        # Missing Court_Date - incomplete data
    )
    
    score, status = scorer.score_arrest(record3)
    record3.Lead_Score = score
    record3.Lead_Status = status
    print_record_summary(record3, scorer)
    
    # Example 4: DISQUALIFIED - ROR bond
    print("\n\n### EXAMPLE 4: DISQUALIFIED (Released on own recognizance)")
    record4 = ArrestRecord(
        Booking_Number="2025-001237",
        Full_Name="DAVIS, MICHAEL JAMES",
        County="Hendry",
        Bond_Amount="$0",
        Bond_Type="ROR",
        Status="RELEASED",
        Charges="Disorderly Conduct",
        Court_Date="2025-12-05"
    )
    
    score, status = scorer.score_arrest(record4)
    record4.Lead_Score = score
    record4.Lead_Status = status
    print_record_summary(record4, scorer)
    
    # Example 5: DISQUALIFIED - Severe charge
    print("\n\n### EXAMPLE 5: DISQUALIFIED (Severe charge - murder)")
    record5 = ArrestRecord(
        Booking_Number="2025-001238",
        Full_Name="MARTINEZ, CARLOS",
        County="Lee",
        Bond_Amount="$0",
        Bond_Type="NO BOND",
        Status="IN CUSTODY",
        Charges="First Degree Murder",
        Court_Date="2025-12-20"
    )
    
    score, status = scorer.score_arrest(record5)
    record5.Lead_Score = score
    record5.Lead_Status = status
    print_record_summary(record5, scorer)
    
    # Example 6: HOT LEAD - High bond, in custody
    print("\n\n### EXAMPLE 6: HOT LEAD (High bond, surety, in custody)")
    record6 = ArrestRecord(
        Booking_Number="2025-001239",
        Full_Name="GARCIA, MARIA ELENA",
        First_Name="MARIA",
        Last_Name="GARCIA",
        DOB="1988-09-10",
        County="Manatee",
        Bond_Amount="$25,000",
        Bond_Type="SURETY BOND",
        Status="IN CUSTODY",
        Charges="Aggravated Battery, Resisting Arrest",
        Court_Date="2025-12-18",
        Full_Name="GARCIA, MARIA ELENA"
    )
    
    score, status = scorer.score_arrest(record6)
    record6.Lead_Score = score
    record6.Lead_Status = status
    print_record_summary(record6, scorer)
    
    # Example 7: WARM LEAD - Very high bond (over 100K)
    print("\n\n### EXAMPLE 7: WARM LEAD (Very high bond - over $100K)")
    record7 = ArrestRecord(
        Booking_Number="2025-001240",
        Full_Name="ANDERSON, THOMAS LEE",
        County="Sarasota",
        Bond_Amount="$150,000",
        Bond_Type="SURETY",
        Status="IN CUSTODY",
        Charges="Trafficking in Controlled Substance",
        Court_Date="2025-12-22"
    )
    
    score, status = scorer.score_arrest(record7)
    record7.Lead_Score = score
    record7.Lead_Status = status
    print_record_summary(record7, scorer)
    
    # Summary statistics
    print("\n\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    all_records = [record1, record2, record3, record4, record5, record6, record7]
    
    hot_count = sum(1 for r in all_records if r.Lead_Status == "Hot")
    warm_count = sum(1 for r in all_records if r.Lead_Status == "Warm")
    cold_count = sum(1 for r in all_records if r.Lead_Status == "Cold")
    disq_count = sum(1 for r in all_records if r.Lead_Status == "Disqualified")
    
    print(f"\nTotal Records: {len(all_records)}")
    print(f"  Hot Leads: {hot_count}")
    print(f"  Warm Leads: {warm_count}")
    print(f"  Cold Leads: {cold_count}")
    print(f"  Disqualified: {disq_count}")
    
    qualified_count = sum(1 for r in all_records if r.is_qualified(70))
    print(f"\nQualified for Qualified_Arrests sheet (score >= 70): {qualified_count}")
    
    avg_score = sum(r.Lead_Score for r in all_records) / len(all_records)
    print(f"Average Score: {avg_score:.1f}")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
