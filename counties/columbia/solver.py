#!/usr/bin/env python3
"""
Columbia County Solver — SmartCOP/SmartWEB Scraper

Uses the shared SmartCOP parser (core/smartcop_parser.py) to scrape
the Columbia County jail roster. No browser required.

Source: http://50.204.15.10/smartwebclient/Jail.aspx
Platform: SmartCOP/SmartWEB (ASP.NET) — accessed via IP
"""

import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.smartcop_parser import scrape_smartcop

BASE_URL = "http://50.204.15.10"
JAIL_PATH = "/smartwebclient/Jail.aspx"


def scrape_columbia(days_back=7, max_pages=10):
    """Scrape Columbia County jail roster via SmartCOP."""
    return scrape_smartcop(
        base_url=BASE_URL,
        county="Columbia",
        jail_path=JAIL_PATH,
    )


if __name__ == "__main__":
    records = scrape_columbia()
    print(json.dumps(records, indent=2))
