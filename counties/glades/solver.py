#!/usr/bin/env python3
"""
Glades County Solver — SmartCOP/SmartWEB Scraper

Uses the shared SmartCOP parser (core/smartcop_parser.py) to scrape
the Glades County jail roster. No browser required.

Source: http://smartweb.gladessheriff.org/smartwebclient/Jail.aspx
Platform: SmartCOP/SmartWEB (ASP.NET)
"""

import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.smartcop_parser import scrape_smartcop

BASE_URL = "http://smartweb.gladessheriff.org"
JAIL_PATH = "/smartwebclient/Jail.aspx"


def scrape_glades(days_back=7, max_pages=10):
    """Scrape Glades County jail roster via SmartCOP."""
    return scrape_smartcop(
        base_url=BASE_URL,
        county="Glades",
        jail_path=JAIL_PATH,
    )


if __name__ == "__main__":
    records = scrape_glades()
    print(json.dumps(records, indent=2))
