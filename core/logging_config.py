"""
Structured logging — county-aware, JSON-lines format.

Usage:
    from core.logging_config import get_logger
    logger = get_logger("charlotte")
    logger.info("Scraped 42 records", extra={"count": 42})
"""

import logging
import json
import sys
from pathlib import Path
from datetime import datetime


REPO_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_ROOT / "logs"


class JSONLineFormatter(logging.Formatter):
    """Format log records as JSON lines for easy machine parsing."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "county": getattr(record, "county", "system"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        # Include any extra fields
        if hasattr(record, "count"):
            log_entry["count"] = record.count
        if hasattr(record, "error"):
            log_entry["error"] = str(record.error)
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def get_logger(county_name: str = "system") -> logging.Logger:
    """
    Get a county-aware logger that writes to stderr and a JSONL log file.

    Args:
        county_name: County identifier for log file and context.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(f"scraper.{county_name}")
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)

    # Console handler (human-readable)
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(
        f"[%(levelname)s] [{county_name}] %(message)s"
    ))
    logger.addHandler(console)

    # File handler (JSONL)
    log_dir = LOGS_DIR / county_name
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONLineFormatter())
    logger.addHandler(file_handler)

    return logger


# Alias for backward compatibility — all county runners import this name
setup_logging = get_logger
