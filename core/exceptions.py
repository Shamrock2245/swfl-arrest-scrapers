"""
Custom exceptions for the scraper system.
All county scrapers and core modules should use these instead of bare exceptions.
"""


class ScraperError(Exception):
    """Base exception for all scraper errors."""
    pass


class ScraperBlocked(ScraperError):
    """Raised when anti-bot detection triggers (Cloudflare, CAPTCHA, IP ban)."""
    pass


class SiteDown(ScraperError):
    """Raised when the jail website is unreachable or returning 5xx errors."""
    pass


class ParseError(ScraperError):
    """Raised when HTML/JSON parsing fails to extract expected data."""
    pass


class SchemaValidationError(ScraperError):
    """Raised when a record fails validation against the 34-column schema."""
    pass


class WriterError(ScraperError):
    """Raised when writing to Google Sheets, MongoDB, or local files fails."""
    pass


class ConfigError(ScraperError):
    """Raised when county configuration is missing or invalid."""
    pass


class DuplicateRecordError(ScraperError):
    """Raised when a record is a duplicate (Booking_Number + County already exists)."""
    pass
