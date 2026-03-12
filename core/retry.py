"""
Retry decorator with exponential backoff and jitter.
Use this for ALL network calls — never make raw requests without retry.

Usage:
    from core.retry import retry

    @retry(max_attempts=3, backoff=2.0)
    def fetch_page(url):
        ...
"""

import time
import random
import functools
import sys
from core.exceptions import ScraperBlocked, SiteDown


def retry(max_attempts=3, backoff=2.0, jitter=True, exceptions=(Exception,)):
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including first try)
        backoff: Base backoff multiplier in seconds
        jitter: If True, add random jitter to backoff
        exceptions: Tuple of exception types to retry on
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        sys.stderr.write(
                            f"⚠️ {func.__name__} failed after {max_attempts} attempts: {e}\n"
                        )
                        raise
                    wait = backoff * (2 ** (attempt - 1))
                    if jitter:
                        wait += random.uniform(0, wait * 0.5)
                    sys.stderr.write(
                        f"🔄 {func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {wait:.1f}s...\n"
                    )
                    time.sleep(wait)
            raise last_exception
        return wrapper
    return decorator
