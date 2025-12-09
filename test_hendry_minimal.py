#!/usr/bin/env python3
import sys
sys.stderr.write("Script started\\n")
sys.stderr.flush()

from DrissionPage import ChromiumPage, ChromiumOptions
sys.stderr.write("Imports successful\\n")
sys.stderr.flush()

co = ChromiumOptions()
co.auto_port()
sys.stderr.write("Options created\\n")
sys.stderr.flush()

page = ChromiumPage(co)
sys.stderr.write("Page created\\n")
sys.stderr.flush()

page.get('https://www.hendrysheriff.org/inmateSearch')
sys.stderr.write(f"Page loaded, title: {page.title}\\n")
sys.stderr.flush()

page.quit()
sys.stderr.write("Done\\n")
