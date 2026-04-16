#!/usr/bin/env python3
"""
Dixie County Solver — SmartCOP/SmartWEB Scraper

Uses the shared SmartCOP parser (core/smartcop_parser.py) to scrape
the Dixie County jail roster. No browser required.

Source: http://smartcop.dixiecountysheriff.com/smartwebclient/Jail.aspx
Platform: SmartCOP/SmartWEB (ASP.NET)
"""

import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.smartcop_parser import scrape_smartcop

BASE_URL = "http://smartcop.dixiecountysheriff.com"
JAIL_PATH = "/smartwebclient/Jail.aspx"


def scrape_dixie(days_back=7, max_pages=10):
    """Scrape Dixie County jail roster via SmartCOP."""
    return scrape_smartcop(
        base_url=BASE_URL,
        county="Dixie",
        jail_path=JAIL_PATH,
    )


if __name__ == "__main__":
    records = scrape_dixie()
    print(json.dumps(records, indent=2))
