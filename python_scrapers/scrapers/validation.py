#!/usr/bin/env python3
"""
Validation Module for SWFL Arrest Scrapers

Provides schema validation and data quality checks for arrest records
before saving to ensure downstream processes receive clean, complete data.

Author: SWFL Arrest Scrapers Team
Date: December 26, 2025
"""

import re
from typing import Dict, List, Tuple


# Required fields that MUST be present for a valid record
REQUIRED_FIELDS = [
    'Booking_Number',
    'Full_Name',
    'County'
]

# Recommended fields that should be present for quality
RECOMMENDED_FIELDS = [
    'First_Name',
    'Last_Name',
    'Booking_Date',
    'Charges',
    'Bond_Amount'
]

# All known schema fields
ALL_SCHEMA_FIELDS = [
    'Booking_Number', 'Full_Name', 'First_Name', 'Last_Name', 'DOB',
    'Sex', 'Race', 'Arrest_Date', 'Time', 'Booking_Date', 'Booking_Time',
    'Agency', 'Address', 'City', 'State', 'ZIP', 'Zipcode',
    'Charges', 'Charge_1', 'Charge_2', 'Bond_Amount', 'Bond_Type',
    'Status', 'Court_Date', 'Case_Number', 'Mugshot_URL',
    'County', 'Court_Location', 'Detail_URL', 'Lead_Score', 'Lead_Status',
    'Facility', 'Height', 'Weight'
]


def validate_record(record: Dict, county: str, strict: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate an arrest record against schema requirements.
    
    Args:
        record: Dictionary containing arrest record data
        county: County name for context in error messages
        strict: If True, also require RECOMMENDED_FIELDS
    
    Returns:
        Tuple of (is_valid, list_of_issues)
        is_valid: True if record passes validation
        list_of_issues: List of validation error/warning messages
    """
    issues = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in record or not record[field]:
            issues.append(f"CRITICAL: Missing required field '{field}'")
    
    # Check recommended fields
    for field in RECOMMENDED_FIELDS:
        if field not in record or not record[field]:
            issues.append(f"WARNING: Missing recommended field '{field}'")
    
    # Validate Booking_Number format
    if 'Booking_Number' in record and record['Booking_Number']:
        bn = str(record['Booking_Number'])
        if len(bn) < 3:
            issues.append(f"WARNING: Booking_Number '{bn}' seems too short")
    
    # Validate Full_Name
    if 'Full_Name' in record and record['Full_Name']:
        name = record['Full_Name']
        if len(name) < 3:
            issues.append(f"WARNING: Full_Name '{name}' seems too short")
        if name.upper() == name and len(name) > 5:
            issues.append(f"INFO: Full_Name is all uppercase: '{name}'")
    
    # Validate Bond_Amount
    if 'Bond_Amount' in record and record['Bond_Amount']:
        try:
            bond = float(str(record['Bond_Amount']).replace('$', '').replace(',', ''))
            if bond < 0:
                issues.append(f"WARNING: Negative bond amount: {bond}")
            if bond > 10000000:
                issues.append(f"WARNING: Unusually high bond amount: {bond}")
        except ValueError:
            issues.append(f"WARNING: Invalid bond amount format: '{record['Bond_Amount']}'")
    
    # Validate County field
    if 'County' in record:
        if record['County'] != county:
            issues.append(f"WARNING: County mismatch: expected '{county}', got '{record['County']}'")
    else:
        issues.append(f"CRITICAL: Missing County field (should be '{county}')")
    
    # Validate dates (basic format check)
    date_fields = ['DOB', 'Arrest_Date', 'Booking_Date', 'Court_Date']
    for field in date_fields:
        if field in record and record[field]:
            date_str = str(record[field])
            # Check for common date patterns
            if not (re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', date_str) or
                    re.match(r'\d{4}-\d{2}-\d{2}', date_str) or
                    re.match(r'\d{1,2}-\d{1,2}-\d{2,4}', date_str)):
                issues.append(f"WARNING: {field} has unusual format: '{date_str}'")
    
    # Validate URLs
    url_fields = ['Mugshot_URL', 'Detail_URL']
    for field in url_fields:
        if field in record and record[field]:
            url = str(record[field])
            if not (url.startswith('http://') or url.startswith('https://') or url.startswith('data:')):
                issues.append(f"WARNING: {field} doesn't start with http/https/data: '{url[:50]}'")
    
    # Check for empty strings (should be None or omitted)
    for key, value in record.items():
        if value == '':
            issues.append(f"INFO: Field '{key}' is empty string (should be None or omitted)")
    
    # Determine if valid
    critical_issues = [i for i in issues if i.startswith('CRITICAL')]
    
    if strict:
        # In strict mode, warnings also fail validation
        warning_issues = [i for i in issues if i.startswith('WARNING')]
        is_valid = len(critical_issues) == 0 and len(warning_issues) == 0
    else:
        # In normal mode, only critical issues fail validation
        is_valid = len(critical_issues) == 0
    
    return is_valid, issues


def validate_batch(records: List[Dict], county: str, strict: bool = False) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Validate a batch of records and separate valid from invalid.
    
    Args:
        records: List of arrest record dictionaries
        county: County name for validation
        strict: If True, apply strict validation
    
    Returns:
        Tuple of (valid_records, invalid_records, stats)
        valid_records: List of records that passed validation
        invalid_records: List of records that failed validation
        stats: Dictionary with validation statistics
    """
    valid = []
    invalid = []
    total_issues = []
    
    for record in records:
        is_valid, issues = validate_record(record, county, strict)
        
        if is_valid:
            valid.append(record)
        else:
            invalid.append({
                'record': record,
                'issues': issues
            })
        
        total_issues.extend(issues)
    
    stats = {
        'total': len(records),
        'valid': len(valid),
        'invalid': len(invalid),
        'validation_rate': len(valid) / len(records) * 100 if records else 0,
        'total_issues': len(total_issues),
        'critical_issues': len([i for i in total_issues if i.startswith('CRITICAL')]),
        'warnings': len([i for i in total_issues if i.startswith('WARNING')]),
        'info': len([i for i in total_issues if i.startswith('INFO')])
    }
    
    return valid, invalid, stats


def get_missing_fields(record: Dict) -> List[str]:
    """
    Get list of schema fields that are missing from a record.
    
    Args:
        record: Arrest record dictionary
    
    Returns:
        List of missing field names
    """
    return [field for field in ALL_SCHEMA_FIELDS if field not in record or not record[field]]


def get_data_completeness_score(record: Dict) -> float:
    """
    Calculate data completeness score (0-100).
    
    Higher score = more fields populated.
    Used for lead scoring and data quality metrics.
    
    Args:
        record: Arrest record dictionary
    
    Returns:
        Completeness score (0-100)
    """
    total_fields = len(ALL_SCHEMA_FIELDS)
    populated_fields = sum(1 for field in ALL_SCHEMA_FIELDS if field in record and record[field])
    
    return (populated_fields / total_fields) * 100


def sanitize_record(record: Dict) -> Dict:
    """
    Clean and sanitize a record for safe storage.
    
    - Remove empty strings (replace with None)
    - Strip whitespace from strings
    - Remove None values
    - Ensure County field is uppercase
    
    Args:
        record: Arrest record dictionary
    
    Returns:
        Sanitized record dictionary
    """
    sanitized = {}
    
    for key, value in record.items():
        # Skip None values
        if value is None:
            continue
        
        # Convert empty strings to None and skip
        if value == '':
            continue
        
        # Strip whitespace from strings
        if isinstance(value, str):
            value = value.strip()
            
            # Skip if now empty after stripping
            if not value:
                continue
        
        # Uppercase County field
        if key == 'County' and isinstance(value, str):
            value = value.upper()
        
        sanitized[key] = value
    
    return sanitized


def format_validation_report(issues: List[str]) -> str:
    """
    Format validation issues into a readable report.
    
    Args:
        issues: List of validation issue messages
    
    Returns:
        Formatted report string
    """
    if not issues:
        return "✅ No validation issues"
    
    critical = [i for i in issues if i.startswith('CRITICAL')]
    warnings = [i for i in issues if i.startswith('WARNING')]
    info = [i for i in issues if i.startswith('INFO')]
    
    report = []
    
    if critical:
        report.append(f"❌ CRITICAL ISSUES ({len(critical)}):")
        for issue in critical:
            report.append(f"  - {issue}")
    
    if warnings:
        report.append(f"⚠️  WARNINGS ({len(warnings)}):")
        for issue in warnings:
            report.append(f"  - {issue}")
    
    if info:
        report.append(f"ℹ️  INFO ({len(info)}):")
        for issue in info:
            report.append(f"  - {issue}")
    
    return "\n".join(report)


# Example usage
if __name__ == "__main__":
    # Test record
    test_record = {
        'Booking_Number': '2025-12345',
        'Full_Name': 'DOE, JOHN',
        'First_Name': 'JOHN',
        'Last_Name': 'DOE',
        'County': 'Charlotte',
        'Booking_Date': '12/26/2025',
        'Charges': 'DUI | POSSESSION',
        'Bond_Amount': '5000'
    }
    
    is_valid, issues = validate_record(test_record, 'Charlotte')
    
    print(f"Valid: {is_valid}")
    print(format_validation_report(issues))
    print(f"\nCompleteness Score: {get_data_completeness_score(test_record):.1f}%")
