#!/usr/bin/env python3
"""
SWFL Arrest Scrapers - Unified Pipeline Runner

Runs all county scrapers sequentially and writes results to Google Sheets.
Currently supports:
1. Sarasota (Python)
2. Charlotte (Python)
3. Hendry (Python)

Usage:
    python run_pipeline.py [--days-back N]
"""

import sys
import os
import subprocess
import argparse
import time

def run_scraper(script_name, args=None):
    """Run a scraper script and stream its output."""
    script_path = os.path.join(os.path.dirname(__file__), 'scrapers', script_name)
    
    cmd = ['python3', script_path]
    if args:
        cmd.extend(args)
        
    print(f"\n{'='*60}")
    print(f"🚀 STARTING: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        # We use p.wait() instead of capture_output to stream output in real-time
        p = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
        p.communicate()
        
        if p.returncode == 0:
            print(f"\n✅ FINISHED: {script_name}")
        else:
            print(f"\n❌ FAILED: {script_name} (Code {p.returncode})")
            
    except Exception as e:
        print(f"\n❌ ERROR running {script_name}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Run SWFL Arrest Scrapers Pipeline')
    parser.add_argument('--days-back', type=str, default='1', help='Days back to scrape (where supported)')
    args = parser.parse_args()
    
    # 1. Sarasota
    # run_sarasota.py accepts days_back arg
    run_scraper('run_sarasota.py', [args.days_back])
    
    # 2. Charlotte
    # run_charlotte.py does not currently accept args, runs default logic
    run_scraper('run_charlotte.py')
    
    # 3. Hendry
    # run_hendry.py does not currently accept args
    run_scraper('run_hendry.py')
    
    # 4. Manatee
    # run_manatee.py accepts days_back and max_pages
    # We'll use defaults or derive from days-back
    # If explicit days back is large, we might want to increase max_pages?
    # For now, pass days_back
    run_scraper('run_manatee.py', ['--days-back', args.days_back])
    
    print(f"\n{'='*60}")
    print(f"🎉 PIPELINE COMPLETE")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
