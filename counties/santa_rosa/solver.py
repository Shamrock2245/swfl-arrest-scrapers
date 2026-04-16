#!/usr/bin/env python3
"""
Santa Rosa County Solver — SmartCOP/SmartWEB Scraper

Uses the shared SmartCOP parser (core/smartcop_parser.py) to scrape
the Santa Rosa County jail roster. No browser required.

Source: http://smartweb.santarosasheriff.org/smartwebclient/Jail.aspx
Platform: SmartCOP/SmartWEB (ASP.NET)
"""

import sys
import json
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.smartcop_parser import scrape_smartcop

BASE_URL = "http://smartweb.santarosasheriff.org"
JAIL_PATH = "/smartwebclient/Jail.aspx"


def scrape_santa_rosa(days_back=7, max_pages=10):
    """Scrape Santa Rosa County jail roster via SmartCOP."""
    return scrape_smartcop(
        base_url=BASE_URL,
        county="Santa Rosa",
        jail_path=JAIL_PATH,
    )


if __name__ == "__main__":
    records = scrape_santa_rosa()
    print(json.dumps(records, indent=2))
