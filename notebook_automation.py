"""
Gemini Notebook Browser Automation
===================================
Uses Selenium + Firefox to automate Google Notebook:
  1. Create a new notebook
  2. Search notebooks
  3. Open a notebook & use Deep Research prompt

Usage:
  python notebook_automation.py --action create
  python notebook_automation.py --action search --query "your search term"
  python notebook_automation.py --action deep-research --query "your research topic"
"""

import os
import sys
import time
import argparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

FIREFOX_PROFILE_PATH = r"C:\Users\SUBHAJIT PAL\AppData\Roaming\Mozilla\Firefox\Profiles\hqrp69r2.default-release-1787274643325"
BASE_URL = "https://notebook.google.com/"
WAIT_TIMEOUT = 20


class NotebookAutomation:
    def __init__(self):
        self.driver = None

    def start_browser(self):
        print("[*] Starting Firefox with existing profile...")
        options = Options()
        options.profile = FIREFOX_PROFILE_PATH
        self.driver = webdriver.Firefox(options=options)
        self.driver.maximize_window()
        print("[OK] Browser started.")

    def navigate_home(self):
        print(f"[*] Navigating to {BASE_URL} ...")
        self.driver.get(BASE_URL)
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.create-new-button, mat-card.create-new-action-button"))
        )
        time.sleep(2)
        print(f"[OK] Page loaded: {self.driver.title}")

    def close_browser(self):
        if self.driver:
            print("[*] Closing browser...")
            self.driver.quit()
            print("[OK] Browser closed.")

    def create_notebook(self):
        self.navigate_home()
        print("[*] Looking for 'Create new' button...")
        try:
            create_btn = WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.create-new-button"))
            )
            create_btn.click()
            print("[OK] Clicked 'Create new' button.")
        except TimeoutException:
            try:
                create_card = self.driver.find_element(By.CSS_SELECTOR, "mat-card.create-new-action-button")
                create_card.click()
                print("[OK] Clicked 'Create new' card.")
            except NoSuchElementException:
                create_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Create new notebook"]')
                create_btn.click()
                print("[OK] Clicked 'Create new notebook' (aria-label).")

        time.sleep(5)
        print(f"[OK] New notebook created: {self.driver.current_url}")
        return self.driver.current_url


def main():
    parser = argparse.ArgumentParser(description="Gemini Notebook Automation")
    parser.add_argument("--action", choices=["create", "search", "deep-research"], required=True)
    parser.add_argument("--query", type=str, default="")
    args = parser.parse_args()

    bot = NotebookAutomation()
    bot.start_browser()
    try:
        if args.action == "create":
            bot.create_notebook()
    finally:
        bot.close_browser()


if __name__ == "__main__":
    main()
