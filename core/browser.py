"""
Browser session management — creates configured DrissionPage browser instances.

Usage:
    from core.browser import create_browser
    page = create_browser(config)
"""

import os
import sys
from DrissionPage import ChromiumPage, ChromiumOptions


def create_browser(config: dict = None) -> ChromiumPage:
    """
    Create and configure a DrissionPage browser session.

    Auto-detects Docker environment via CHROME_PATH env var.

    Args:
        config: Merged county config dict. Uses browser settings from it.

    Returns:
        Configured ChromiumPage instance.
    """
    if config is None:
        config = {}

    browser_config = config.get("browser", {})
    headless = config.get("headless", browser_config.get("headless", True))
    window_size = browser_config.get("window_size", "1920x1080")
    user_agent = browser_config.get(
        "user_agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    co = ChromiumOptions()
    co.auto_port()

    # Docker: set Chromium binary path from env
    chrome_path = os.getenv("CHROME_PATH")
    if chrome_path:
        co.set_browser_path(chrome_path)

    # Headless mode — use --headless=new for modern headless
    if headless:
        co.headless(True)
        co.set_argument("--headless=new")

    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-gpu")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument(f"--window-size={window_size.replace('x', ',')}")
    co.set_user_agent(user_agent)

    # Proxy support
    proxy_url = config.get("proxy_url")
    if proxy_url:
        co.set_argument(f"--proxy-server={proxy_url}")

    sys.stderr.write(
        f"🌐 Browser: headless={headless}, chrome_path={chrome_path or 'default'}, size={window_size}\n"
    )

    return ChromiumPage(addr_or_opts=co)
