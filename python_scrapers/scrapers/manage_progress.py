#!/usr/bin/env python3
"""
Progress File Management Utility

Helps manage and clean up progress files (.jsonl) used by scrapers
for resume capability.

Usage:
    python manage_progress.py list                    # List all progress files with stats
    python manage_progress.py archive <county>        # Archive a county's progress file
    python manage_progress.py clean <county>          # Delete a county's progress file
    python manage_progress.py clean-old <days>        # Archive progress files older than N days
    python manage_progress.py stats <county>          # Show detailed stats for a county

Author: SWFL Arrest Scrapers Team
Date: December 26, 2025
"""

import os
import sys
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path


PROGRESS_FILES = {
    'charlotte': 'charlotte_progress.jsonl',
    'hendry': 'hendry_progress.jsonl',
    'sarasota': 'sarasota_progress.jsonl',
    'collier': 'collier_progress.jsonl',
    'lee': 'lee_progress.jsonl'
}


def get_file_stats(filepath):
    """Get statistics about a progress file."""
    if not os.path.exists(filepath):
        return None
    
    stats = {
        'path': filepath,
        'size_bytes': os.path.getsize(filepath),
        'size_mb': os.path.getsize(filepath) / (1024 * 1024),
        'modified': datetime.fromtimestamp(os.path.getmtime(filepath)),
        'record_count': 0,
        'unique_ids': set()
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        stats['record_count'] += 1
                        if 'Booking_Number' in record:
                            stats['unique_ids'].add(record['Booking_Number'])
                    except:
                        pass
        
        stats['unique_count'] = len(stats['unique_ids'])
        stats['duplicate_count'] = stats['record_count'] - stats['unique_count']
    except Exception as e:
        stats['error'] = str(e)
    
    return stats


def list_progress_files():
    """List all progress files with basic stats."""
    print("\n📋 Progress Files Overview\n")
    print(f"{'County':<12} {'File':<30} {'Size':<10} {'Records':<10} {'Modified':<20}")
    print("-" * 90)
    
    for county, filename in PROGRESS_FILES.items():
        stats = get_file_stats(filename)
        
        if stats:
            size_str = f"{stats['size_mb']:.2f} MB" if stats['size_mb'] >= 1 else f"{stats['size_bytes']} B"
            modified_str = stats['modified'].strftime('%Y-%m-%d %H:%M')
            print(f"{county:<12} {filename:<30} {size_str:<10} {stats['record_count']:<10} {modified_str:<20}")
        else:
            print(f"{county:<12} {filename:<30} {'N/A':<10} {'N/A':<10} {'Not found':<20}")
    
    print()


def show_detailed_stats(county):
    """Show detailed statistics for a county's progress file."""
    if county not in PROGRESS_FILES:
        print(f"❌ Unknown county: {county}")
        print(f"Available counties: {', '.join(PROGRESS_FILES.keys())}")
        return
    
    filename = PROGRESS_FILES[county]
    stats = get_file_stats(filename)
    
    if not stats:
        print(f"❌ Progress file not found: {filename}")
        return
    
    print(f"\n📊 Detailed Statistics: {county.title()} County\n")
    print(f"File: {stats['path']}")
    print(f"Size: {stats['size_mb']:.2f} MB ({stats['size_bytes']:,} bytes)")
    print(f"Last Modified: {stats['modified'].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Age: {(datetime.now() - stats['modified']).days} days")
    print(f"\nRecords:")
    print(f"  Total lines: {stats['record_count']}")
    print(f"  Unique IDs: {stats['unique_count']}")
    print(f"  Duplicates: {stats['duplicate_count']}")
    
    if stats['duplicate_count'] > 0:
        dup_pct = (stats['duplicate_count'] / stats['record_count']) * 100
        print(f"  Duplicate rate: {dup_pct:.1f}%")
    
    print()


def archive_progress_file(county):
    """Archive a county's progress file with timestamp."""
    if county not in PROGRESS_FILES:
        print(f"❌ Unknown county: {county}")
        return
    
    filename = PROGRESS_FILES[county]
    
    if not os.path.exists(filename):
        print(f"❌ Progress file not found: {filename}")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    archive_name = f"{county}_progress_{timestamp}.jsonl"
    
    try:
        shutil.copy2(filename, archive_name)
        print(f"✅ Archived: {filename} → {archive_name}")
        
        stats = get_file_stats(filename)
        if stats:
            print(f"   {stats['record_count']} records, {stats['size_mb']:.2f} MB")
    except Exception as e:
        print(f"❌ Archive failed: {e}")


def clean_progress_file(county):
    """Delete a county's progress file."""
    if county not in PROGRESS_FILES:
        print(f"❌ Unknown county: {county}")
        return
    
    filename = PROGRESS_FILES[county]
    
    if not os.path.exists(filename):
        print(f"⚠️  Progress file not found: {filename}")
        return
    
    stats = get_file_stats(filename)
    
    try:
        os.remove(filename)
        print(f"✅ Deleted: {filename}")
        if stats:
            print(f"   {stats['record_count']} records removed, {stats['size_mb']:.2f} MB freed")
    except Exception as e:
        print(f"❌ Delete failed: {e}")


def clean_old_files(days):
    """Archive progress files older than N days."""
    try:
        days = int(days)
    except ValueError:
        print(f"❌ Invalid days value: {days}")
        return
    
    cutoff = datetime.now() - timedelta(days=days)
    print(f"\n🗑️  Archiving files older than {days} days (before {cutoff.strftime('%Y-%m-%d')})\n")
    
    archived_count = 0
    
    for county, filename in PROGRESS_FILES.items():
        if not os.path.exists(filename):
            continue
        
        modified = datetime.fromtimestamp(os.path.getmtime(filename))
        
        if modified < cutoff:
            print(f"📦 {county.title()}: {filename} (age: {(datetime.now() - modified).days} days)")
            archive_progress_file(county)
            archived_count += 1
    
    if archived_count == 0:
        print("✅ No files older than threshold found")
    else:
        print(f"\n✅ Archived {archived_count} file(s)")


def show_help():
    """Show usage help."""
    print("""
Progress File Management Utility

Usage:
    python manage_progress.py list                    # List all progress files with stats
    python manage_progress.py archive <county>        # Archive a county's progress file
    python manage_progress.py clean <county>          # Delete a county's progress file
    python manage_progress.py clean-old <days>        # Archive progress files older than N days
    python manage_progress.py stats <county>          # Show detailed stats for a county

Counties:
    charlotte, hendry, sarasota, collier, lee

Examples:
    python manage_progress.py list
    python manage_progress.py stats charlotte
    python manage_progress.py archive hendry
    python manage_progress.py clean sarasota
    python manage_progress.py clean-old 30

Notes:
    - Archive creates a timestamped copy without deleting the original
    - Clean deletes the file permanently
    - clean-old automatically archives old files before deletion
    """)


def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_progress_files()
    
    elif command == 'stats':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_progress.py stats <county>")
            return
        show_detailed_stats(sys.argv[2].lower())
    
    elif command == 'archive':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_progress.py archive <county>")
            return
        archive_progress_file(sys.argv[2].lower())
    
    elif command == 'clean':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_progress.py clean <county>")
            return
        county = sys.argv[2].lower()
        print(f"⚠️  WARNING: This will permanently delete {PROGRESS_FILES.get(county, 'unknown')}!")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            clean_progress_file(county)
        else:
            print("❌ Cancelled")
    
    elif command == 'clean-old':
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_progress.py clean-old <days>")
            return
        clean_old_files(sys.argv[2])
    
    elif command in ['help', '--help', '-h']:
        show_help()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()
