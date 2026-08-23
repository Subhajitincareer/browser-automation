"""
Browser Automation Script
- Opens https://notebook.google.com/ using Selenium with Firefox
- Uses an existing Firefox profile (already logged in)
- Downloads the page HTML
- Parses it with BeautifulSoup
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup

FIREFOX_PROFILE_PATH = r"C:\Users\SUBHAJIT PAL\AppData\Roaming\Mozilla\Firefox\Profiles\hqrp69r2.default-release-1787274643325"
TARGET_URL = "https://notebook.google.com/"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "notebook_page.html")
PARSED_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "notebook_parsed.txt")

print(f"[*] Using Firefox profile: {FIREFOX_PROFILE_PATH}")

options = Options()
options.profile = FIREFOX_PROFILE_PATH

print(f"[*] Launching Firefox and navigating to {TARGET_URL} ...")
driver = webdriver.Firefox(options=options)

try:
    driver.get(TARGET_URL)
    print("[*] Waiting for page to load...")
    time.sleep(10)

    page_source = driver.page_source
    print(f"[*] Page title: {driver.title}")
    print(f"[*] HTML length: {len(page_source)} characters")

    with open(HTML_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(page_source)
    print(f"[OK] Raw HTML saved to: {HTML_OUTPUT_FILE}")

    soup = BeautifulSoup(page_source, "html.parser")
    title = soup.title.string if soup.title else "No title found"
    all_links = soup.find_all("a", href=True)
    all_headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    all_text = soup.get_text(separator="\n", strip=True)

    with open(PARSED_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f"Page Title: {title}\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Links Found ({len(all_links)}):\n")
        f.write(f"{'-'*40}\n")
        for link in all_links:
            f.write(f"  {link.get_text(strip=True)[:80]:80s} -> {link['href']}\n")
        f.write(f"\nHeadings Found ({len(all_headings)}):\n")
        f.write(f"{'-'*40}\n")
        for heading in all_headings:
            f.write(f"  <{heading.name}> {heading.get_text(strip=True)}\n")
        f.write(f"\nFull Text Content:\n")
        f.write(f"{'-'*40}\n")
        f.write(all_text)

    print(f"[OK] Parsed content saved to: {PARSED_OUTPUT_FILE}")

finally:
    print("\n[*] Closing browser...")
    driver.quit()
    print("[OK] Done!")
