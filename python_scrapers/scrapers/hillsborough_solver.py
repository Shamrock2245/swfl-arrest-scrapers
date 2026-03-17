#!/usr/bin/env python3
"""
Hillsborough County Solver (HCSO) - Headless Login + Scrape

Uses DrissionPage in headless mode to:
1. Navigate to HCSO Arrest Inquiry login page
2. Login with HCSO_EMAIL / HCSO_PASSWORD
3. Perform search for recent arrests
4. Parse results across paginated table
5. Output JSON to stdout

Requires: HCSO_EMAIL, HCSO_PASSWORD env vars

Author: SWFL Arrest Scrapers Team
Date: March 2026
"""

import sys
import json
import time
import os
import datetime
from bs4 import BeautifulSoup

# DrissionPage import
from DrissionPage import ChromiumPage, ChromiumOptions


def setup_browser():
    """Create headless Chrome browser via DrissionPage."""
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')
    co.set_argument('--window-size=1920,1080')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return ChromiumPage(co)


def login_hcso(page, email, password):
    """Log into the HCSO Arrest Inquiry portal (handles reCAPTCHA v2 checkbox)."""
    login_url = "https://webapps.hcso.tampa.fl.us/arrestinquiry/Account/Login"
    sys.stderr.write(f"🔑 Navigating to login page...\n")
    page.get(login_url)
    time.sleep(3)

    # Fill email
    email_field = page.ele('#Email', timeout=10)
    if not email_field:
        sys.stderr.write("❌ Could not find email field\n")
        return False
    email_field.clear()
    email_field.input(email)

    # Fill password
    pwd_field = page.ele('#Password', timeout=5)
    if not pwd_field:
        sys.stderr.write("❌ Could not find password field\n")
        return False
    pwd_field.clear()
    pwd_field.input(password)

    # Toggle "Remember me" checkbox
    remember_me = page.ele('#RememberMe', timeout=3)
    if remember_me:
        try:
            remember_me.click()
            sys.stderr.write("✅ Remember Me toggled\n")
        except Exception:
            sys.stderr.write("⚠️  Could not toggle Remember Me\n")

    # Handle reCAPTCHA v2 checkbox (inside iframe)
    sys.stderr.write("🤖 Looking for reCAPTCHA...\n")
    recaptcha_solved = False
    try:
        # reCAPTCHA lives inside an iframe — find it
        recaptcha_iframe = page.ele('tag:iframe@@title=reCAPTCHA', timeout=5)
        if not recaptcha_iframe:
            # Try alternate selectors
            recaptcha_iframe = page.ele('tag:iframe@@src:recaptcha', timeout=3)
        
        if recaptcha_iframe:
            sys.stderr.write("   Found reCAPTCHA iframe, clicking checkbox...\n")
            # Switch into the iframe and click the checkbox
            iframe_page = recaptcha_iframe.ele('tag:div@@class:recaptcha-checkbox-border', timeout=5)
            if iframe_page:
                iframe_page.click()
                sys.stderr.write("   Clicked reCAPTCHA checkbox\n")
                time.sleep(3)
                recaptcha_solved = True
            else:
                # Try clicking the span with recaptcha-checkbox role
                checkbox = recaptcha_iframe.ele('#recaptcha-anchor', timeout=3)
                if checkbox:
                    checkbox.click()
                    sys.stderr.write("   Clicked reCAPTCHA anchor\n")
                    time.sleep(3)
                    recaptcha_solved = True
                else:
                    sys.stderr.write("   ⚠️  Could not find checkbox inside iframe\n")
        else:
            sys.stderr.write("   No reCAPTCHA iframe found (may not be required)\n")
            recaptcha_solved = True  # No CAPTCHA = proceed
    except Exception as e:
        sys.stderr.write(f"   ⚠️  reCAPTCHA handling error: {e}\n")

    if not recaptcha_solved:
        sys.stderr.write("⚠️  reCAPTCHA may not be solved, attempting login anyway...\n")

    # Wait a moment for reCAPTCHA to process
    time.sleep(2)

    # Click login button
    login_btn = page.ele('tag:button@@text():Log in', timeout=5) or page.ele('tag:input@@type=submit', timeout=3)
    if login_btn:
        login_btn.click()
    else:
        # Try form submit
        pwd_field.input('\n')
    
    time.sleep(5)
    
    # Check if login succeeded
    page_html = page.html
    current_url = page.url
    sys.stderr.write(f"   Post-login URL: {current_url}\n")
    
    if 'Log out' in page_html or 'Welcome' in page_html or 'Search' in page_html:
        sys.stderr.write("✅ Login successful\n")
        return True
    elif 'Invalid' in page_html or 'incorrect' in page_html.lower():
        sys.stderr.write("❌ Invalid credentials (may be reCAPTCHA block)\n")
        # Dump page snippet for debugging
        sys.stderr.write(f"   Page title: {page.title}\n")
        return False
    else:
        sys.stderr.write(f"⚠️  Login status unclear. Current URL: {current_url}\n")
        # Try to proceed anyway
        return 'arrestinquiry' in current_url.lower()
