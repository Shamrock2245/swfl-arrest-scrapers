"""
Anti-bot evasion utilities — Cloudflare waits, fingerprint helpers.

Usage:
    from core.stealth import wait_for_cloudflare
    if not wait_for_cloudflare(page):
        raise ScraperBlocked("Cloudflare did not clear")
"""

import sys
import time


def wait_for_cloudflare(page, max_wait: int = 20) -> bool:
    """
    Wait for Cloudflare challenge to clear, if present.

    Args:
        page: DrissionPage ChromiumPage instance
        max_wait: Maximum seconds to wait

    Returns:
        True if page loaded successfully, False if challenge didn't clear.
    """
    waited = 0
    while waited < max_wait:
        title = page.title.lower() if page.title else ""
        if "just a moment" not in title and "checking" not in title:
            return True
        sys.stderr.write(f"   ⏳ Cloudflare challenge... ({waited}/{max_wait}s)\n")
        time.sleep(1)
        waited += 1
    return False


def random_delay(min_seconds: float = 0.5, max_seconds: float = 2.0):
    """Add a random delay to avoid detection patterns."""
    import random
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def clean_text(text: str) -> str:
    """Clean and normalize text from scraped pages."""
    if not text:
        return ""
    return " ".join(text.strip().split())
