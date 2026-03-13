"""
Slack notifier — sends alerts and completion messages to Slack channels.

Usage:
    from core.writers.slack_notifier import notify_completion, notify_error
    notify_completion("charlotte", stats)
"""

import os
import json
import sys

try:
    from urllib.request import Request, urlopen
except ImportError:
    Request = None
    urlopen = None


def _send_slack_message(text: str, webhook_url: str = None):
    """Send a message to Slack via webhook."""
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        sys.stderr.write("⚠️ SLACK_WEBHOOK_URL not set, skipping notification\n")
        return

    payload = json.dumps({"text": text}).encode("utf-8")
    req = Request(url, data=payload, headers={"Content-type": "application/json"})
    try:
        urlopen(req, timeout=10)
    except Exception as e:
        sys.stderr.write(f"⚠️ Slack notification failed: {e}\n")


def notify_completion(county_name: str, stats: dict, webhook_url: str = None):
    """Send a scraper completion message to Slack."""
    new = stats.get("new_records", 0)
    updated = stats.get("updated_records", 0)
    qualified = stats.get("qualified_records", 0)
    text = (
        f"✅ *{county_name.title()}* scraper complete — "
        f"{new} new, {updated} updated, {qualified} qualified"
    )
    _send_slack_message(text, webhook_url)


def notify_error(county_name: str, error: str, webhook_url: str = None):
    """Send a scraper error message to Slack."""
    text = f"❌ *{county_name.title()}* scraper failed — {error}"
    _send_slack_message(text, webhook_url)


def notify_slack(county: str, message: str, level: str = "info", webhook_url: str = None):
    """
    Generic Slack notification used by county runners.

    Args:
        county: County name (for context)
        message: Pre-formatted message text
        level: 'success', 'error', 'warning', or 'info'
        webhook_url: Override Slack webhook URL
    """
    _send_slack_message(message, webhook_url)
