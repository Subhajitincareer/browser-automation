"""
Gemini Notebook Full Pipeline
==============================
1. Opens a specific notebook in Firefox
2. Types a prompt in the chat box
3. Clicks Send and waits for the AI answer
4. Extracts the answer text / Studio artifact
5. Sends the answer to Gemini API for HTML conversion
6. Converts the HTML to a styled PDF using Firefox headless

Usage:
  python notebook_pipeline.py --prompt-file cc02_prompt.txt --output-name cc02_sample_paper
"""

import os
import sys
import time
import argparse
import re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

import warnings
warnings.filterwarnings("ignore")

from google import genai
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Redirect temporary files to E:\temp (where 156 GB space is available)
os.environ["TMP"] = r"E:\temp"
os.environ["TEMP"] = r"E:\temp"
os.makedirs(r"E:\temp", exist_ok=True)

# ── Configuration ──────────────────────────────────────────────
FIREFOX_PROFILE_PATH = r"C:\Users\SUBHAJIT PAL\AppData\Roaming\Mozilla\Firefox\Profiles\hqrp69r2.default-release-1787274643325"
DEFAULT_NOTEBOOK_URL = "https://notebook.google.com/notebook/16df629f-4702-4b7e-9dc9-09e5739b77f2"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OUTPUT_DIR = os.path.join(BASE_DIR, "exam_papers")
os.makedirs(OUTPUT_DIR, exist_ok=True)
WAIT_TIMEOUT = 30
MAX_ANSWER_WAIT = 300  # Max seconds to wait for AI answer (5 min for complex prompts)


def start_browser():
    """Launch Firefox with existing profile without running out of disk space."""
    print("[*] Starting Firefox...")
    options = Options()
    options.profile = FIREFOX_PROFILE_PATH
    driver = webdriver.Firefox(options=options)
    driver.maximize_window()
    print("[OK] Browser started.")
    return driver


def open_notebook(driver, url):
    """Navigate to the notebook and wait for it to load."""
    print(f"[*] Opening notebook: {url}")
    driver.get(url)
    WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea.query-box-input"))
    )
    time.sleep(3)
    print(f"[OK] Notebook loaded: {driver.title}")


def send_prompt(driver, prompt_text):
    """Type the prompt in the chat box and click Send."""
    print(f"[*] Sending prompt ({len(prompt_text)} chars)...")
    textarea = WebDriverWait(driver, WAIT_TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.query-box-input"))
    )
    textarea.click()
    time.sleep(0.5)

    if len(prompt_text) > 500:
        print("[*] Using clipboard paste for long prompt...")
        import subprocess
        process = subprocess.Popen(
            ["powershell", "-command", "Set-Clipboard -Value $input"],
            stdin=subprocess.PIPE,
            encoding="utf-8"
        )
        process.communicate(input=prompt_text)
        textarea.clear()
        time.sleep(0.5)

        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(driver).click(textarea).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(3)
    else:
        textarea.clear()
        textarea.send_keys(prompt_text)
        time.sleep(1)

    print("[OK] Prompt pasted.")
    time.sleep(3)

    submitted = False
    for attempt in range(3):
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, 'button.submit-button[aria-label="Submit"]')
            is_disabled = "mat-mdc-button-disabled" in (submit_btn.get_attribute("class") or "")
            if is_disabled and attempt < 2:
                print(f"[*] Submit still disabled, waiting... (attempt {attempt+1})")
                time.sleep(3)
                continue
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", submit_btn)
            submitted = True
            print("[OK] Clicked Send button (JS click).")
            break
        except (NoSuchElementException, Exception) as e:
            if attempt == 2:
                print(f"[*] Submit strategy 1 failed: {e}")
            time.sleep(2)

    if not submitted:
        textarea.send_keys(Keys.RETURN)
        submitted = True
        print("[OK] Submitted via Enter key.")


def wait_for_answer(driver):
    """Wait for the AI to finish generating its answer and extract it."""
    print(f"[*] Waiting for AI answer (max {MAX_ANSWER_WAIT}s)...")

    existing_pairs = driver.find_elements(By.CSS_SELECTOR, "div.chat-message-pair")
    initial_count = len(existing_pairs)
    initial_last_text = existing_pairs[-1].text if existing_pairs else ""
    print(f"    Existing chat pairs: {initial_count}")

    start_time = time.time()
    new_pair = None

    while time.time() - start_time < MAX_ANSWER_WAIT:
        current_pairs = driver.find_elements(By.CSS_SELECTOR, "div.chat-message-pair")
        if len(current_pairs) > initial_count:
            new_pair = current_pairs[-1]
            print("[OK] New answer detected!")
            break
        elif current_pairs and current_pairs[-1].text != initial_last_text:
            new_pair = current_pairs[-1]
            print("[OK] Answer update detected!")
            break
        elif time.time() - start_time > 15 and current_pairs:
            new_pair = current_pairs[-1]
            print("[OK] Using latest chat pair after 15s wait...")
            break
        time.sleep(2)

    if not new_pair:
        print("[!] Timeout waiting for answer.")
        return None

    print("[*] Waiting for answer to finish streaming...")
    last_text = ""
    stable_count = 0

    while stable_count < 3 and (time.time() - start_time) < MAX_ANSWER_WAIT:
        try:
            current_text = new_pair.text
            if current_text == last_text and len(current_text) > 10:
                stable_count += 1
            else:
                stable_count = 0
                last_text = current_text
                if len(current_text) > 10:
                    print(f"    [Streaming...] Received {len(current_text)} chars...")
        except StaleElementReferenceException:
            current_pairs = driver.find_elements(By.CSS_SELECTOR, "div.chat-message-pair")
            if current_pairs:
                new_pair = current_pairs[-1]
        time.sleep(2)

    try:
        answer_elements = new_pair.find_elements(By.CSS_SELECTOR, ".chat-message-content, .response-container, .message-content, .chat-message-text")
        if answer_elements:
            answer_text = answer_elements[-1].text
        else:
            answer_text = new_pair.text
    except Exception as e:
        print(f"[!] Error extracting answer from chat pair: {e}")
        answer_text = new_pair.text if new_pair else ""

    if len(answer_text) < 300 or "Studio" in answer_text or "artifact" in answer_text.lower():
        print("[*] Response may be in Studio panel. Checking Studio / note artifacts...")
        studio_selectors = [
            ".studio-panel", ".artifact-view", "note-viewer", ".note-content",
            "[data-test-id='artifact-content']", ".markdown-content", ".artifact-container"
        ]
        studio_text = ""
        for sel in studio_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    t = el.text.strip()
                    if len(t) > len(studio_text):
                        studio_text = t
            except Exception:
                pass

        if len(studio_text) > len(answer_text):
            print(f"[OK] Found larger content in Studio panel ({len(studio_text)} chars)")
            answer_text = studio_text

    answer_text = re.sub(r'\[\d+\]', '', answer_text)

    print(f"[OK] Answer extracted ({len(answer_text)} chars)")
    print(f"    Preview: {answer_text[:200]}...")

    return answer_text


from google.genai import types

def convert_with_gemini_api(answer_text, prompt_text):
    """Send the answer to Gemini API to convert to well-formatted HTML (with offline fallback)."""
    print("[*] Converting answer to HTML...")

    try:
        if GEMINI_API_KEY:
            client = genai.Client(api_key=GEMINI_API_KEY)
            api_prompt = f"""Convert the following text into a beautiful, well-formatted HTML document. 
            
Requirements:
- Create a complete HTML page with proper <html>, <head>, <body> tags
- Add a professional CSS stylesheet inside <style> tags
- Use a clean, readable font (Google Fonts: Noto Sans Bengali for Bengali text, Inter for English)
- Title should be based on the topic: "{prompt_text}"
- Keep all Bengali text as-is, do not translate

Text to convert:
---
{answer_text}
---

Return ONLY the complete HTML code, no explanation."""

            config = types.GenerateContentConfig(
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )

            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=api_prompt,
                config=config
            )
            html_content = response.text
            html_content = re.sub(r'^```html\s*', '', html_content, flags=re.MULTILINE)
            html_content = re.sub(r'^```\s*$', '', html_content, flags=re.MULTILINE)
            print(f"[OK] Gemini API returned HTML ({len(html_content)} chars)")
            return html_content.strip()
    except Exception as e:
        print(f"[!] Gemini API conversion skipped/failed ({e}). Using local offline HTML builder...")

    # Offline fallback
    from generate_final_outputs import build_html
    return build_html(answer_text)


def save_html(html_content, filename):
    """Save the HTML to a file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] HTML saved: {filepath}")
    return filepath


def convert_to_pdf(html_filepath, pdf_filename):
    """Convert HTML to PDF using Firefox headless print."""
    pdf_filepath = os.path.join(OUTPUT_DIR, pdf_filename)

    print("[*] Converting HTML to PDF (Firefox headless)...")
    try:
        import base64
        options = Options()
        options.add_argument("-headless")
        temp_driver = webdriver.Firefox(options=options)
        try:
            file_url = "file:///" + html_filepath.replace(os.sep, "/")
            temp_driver.get(file_url)
            time.sleep(3)
            result = temp_driver.print_page()
            pdf_data = base64.b64decode(result)
            with open(pdf_filepath, "wb") as f:
                f.write(pdf_data)
            print(f"[OK] PDF saved: {pdf_filepath} ({len(pdf_data)//1024} KB)")
            return pdf_filepath
        finally:
            temp_driver.quit()
    except Exception as e:
        print(f"[!] PDF conversion error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Gemini Notebook Pipeline: Ask -> Answer -> HTML -> PDF")
    parser.add_argument("--prompt", type=str, default="", help="The prompt to send to the notebook chat")
    parser.add_argument("--prompt-file", type=str, default="", help="Path to a text file containing the prompt")
    parser.add_argument("--notebook-url", type=str, default=DEFAULT_NOTEBOOK_URL, help="Notebook URL to open")
    parser.add_argument("--output-name", type=str, default="", help="Base name for output files")
    parser.add_argument("--extract-only", action="store_true", help="Fetch latest answer directly from notebook without sending a new prompt")
    args = parser.parse_args()

    prompt_text = ""
    if args.prompt_file and os.path.exists(args.prompt_file):
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt_text = f.read().strip()
        print(f"[OK] Loaded prompt from file: {args.prompt_file} ({len(prompt_text)} chars)")
    elif args.prompt:
        prompt_text = args.prompt
    elif not args.extract_only:
        parser.error("Either --prompt, --prompt-file, or --extract-only is required")

    if args.output_name:
        base_name = args.output_name
    else:
        base_name = re.sub(r'[^\w\s-]', '', prompt_text[:60]).strip().replace(' ', '_')[:40] if prompt_text else "cc02_sample_paper"
        base_name = base_name or "notebook_output"

    driver = None
    try:
        driver = start_browser()
        open_notebook(driver, args.notebook_url)
        
        if not args.extract_only:
            send_prompt(driver, prompt_text)
            answer_text = wait_for_answer(driver)
        else:
            print("[*] --extract-only mode: Fetching existing answer directly from notebook...")
            # Extract current latest chat/studio content immediately
            existing_pairs = driver.find_elements(By.CSS_SELECTOR, "div.chat-message-pair")
            if existing_pairs:
                latest = existing_pairs[-1]
                answer_elements = latest.find_elements(By.CSS_SELECTOR, ".chat-message-content, .response-container, .message-content, .chat-message-text")
                answer_text = answer_elements[-1].text if answer_elements else latest.text
            else:
                answer_text = ""

            studio_selectors = [
                ".studio-panel", ".artifact-view", "note-viewer", ".note-content",
                "[data-test-id='artifact-content']", ".markdown-content", ".artifact-container"
            ]
            studio_text = ""
            for sel in studio_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    for el in elements:
                        t = el.text.strip()
                        if len(t) > len(studio_text):
                            studio_text = t
                except Exception:
                    pass

            if len(studio_text) > len(answer_text):
                answer_text = studio_text

            answer_text = re.sub(r'\[\d+\]', '', answer_text)
            print(f"[OK] Extracted existing answer ({len(answer_text)} chars)")

        if not answer_text:
            print("[!] No answer received. Exiting.")
            return

        raw_path = os.path.join(OUTPUT_DIR, f"{base_name}_raw.txt")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(answer_text)
        print(f"[OK] Raw answer saved: {raw_path}")

        html_content = convert_with_gemini_api(answer_text, prompt_text[:200])
        html_path = save_html(html_content, f"{base_name}.html")
        pdf_path = convert_to_pdf(html_path, f"{base_name}.pdf")

        print("\n" + "=" * 60)
        print("[DONE] Pipeline complete!")
        print(f"  Raw answer : {raw_path}")
        print(f"  HTML file  : {html_path}")
        if pdf_path:
            print(f"  PDF file   : {pdf_path}")
        print("=" * 60)

    finally:
        if driver:
            print("\n[*] Closing browser...")
            driver.quit()
            print("[OK] Browser closed.")


if __name__ == "__main__":
    main()
