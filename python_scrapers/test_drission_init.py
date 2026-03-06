import os
from DrissionPage import ChromiumPage, ChromiumOptions
import platform

print("Starting test...")
co = ChromiumOptions()

co.auto_port()

print(f"Address after auto_port: {co.address}")

try:
    print("Initializing browser...")
    page = ChromiumPage(addr_or_opts=co)
    print("Browser initialized!")
    page.quit()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
