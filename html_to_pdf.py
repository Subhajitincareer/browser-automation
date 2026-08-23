"""
HTML to PDF Converter
Uses Selenium Firefox to print the HTML file to PDF.
"""
import os
import sys
import time
import base64

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def html_to_pdf_firefox(html_path, pdf_path):
    """Use Firefox's built-in print to PDF."""
    print(f"[*] Converting {os.path.basename(html_path)} to PDF...")

    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)

    try:
        file_url = "file:///" + html_path.replace("\\", "/")
        driver.get(file_url)
        time.sleep(3)

        result = driver.print_page()
        pdf_data = base64.b64decode(result)
        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        print(f"[OK] PDF saved: {pdf_path}")
        print(f"     Size: {len(pdf_data) / 1024:.1f} KB")
        return True

    except Exception as e:
        print(f"[!] Error: {e}")
        return False
    finally:
        driver.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert HTML to PDF")
    parser.add_argument("html_file", help="Path to HTML file")
    parser.add_argument("--output", "-o", help="Output PDF path")
    args = parser.parse_args()

    html_path = os.path.abspath(args.html_file)
    if args.output:
        pdf_path = os.path.abspath(args.output)
    else:
        pdf_path = os.path.splitext(html_path)[0] + ".pdf"

    html_to_pdf_firefox(html_path, pdf_path)
