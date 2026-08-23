"""
Generate Styled HTML and PDF from Raw Bengali CC-02 Question Paper
===================================================================
1. Reads cc02_sample_paper_raw.txt
2. Cleans citations [cite: ...]
3. Formats into a professional examination paper HTML with clean Bengali typography
4. Uses Firefox headless print to convert HTML to PDF
"""

import os
import sys
import re
import time
import base64

os.environ["TMP"] = r"E:\temp"
os.environ["TEMP"] = r"E:\temp"
os.makedirs(r"E:\temp", exist_ok=True)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "exam_papers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

RAW_FILE = os.path.join(BASE_DIR, "cc02_sample_paper_raw.txt")
HTML_FILE = os.path.join(OUTPUT_DIR, "cc02_sample_paper.html")
PDF_FILE = os.path.join(OUTPUT_DIR, "cc02_sample_paper.pdf")

def clean_text(text):
    """Remove citation tags like [cite: 10, 42]"""
    return re.sub(r'\[cite:.*?\]', '', text)

def build_html(raw_content):
    cleaned = clean_text(raw_content)
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    # Format line-by-line into HTML
    html_lines = []
    
    # Header block
    html_lines.append('<div class="exam-header">')
    if len(lines) > 0: html_lines.append(f'<h1>{lines[0]}</h1>')
    if len(lines) > 1: html_lines.append(f'<h2>{lines[1]}</h2>')
    if len(lines) > 2: html_lines.append(f'<h3>{lines[2]}</h3>')
    if len(lines) > 3: html_lines.append(f'<div class="meta-info">{lines[3]}</div>')
    html_lines.append('</div>')

    # Process remaining lines
    current_group = False
    in_mcq_options = False

    for line in lines[4:]:
        if line.startswith("গ্রুপ –") or line.startswith("গ্রুপ-"):
            if in_mcq_options:
                html_lines.append('</div></div>')
                in_mcq_options = False
            html_lines.append(f'<h3 class="group-header">{line}</h3>')
            current_group = True
        elif re.match(r'^[১-৯1-9]+\.', line):
            if in_mcq_options:
                html_lines.append('</div></div>')
                in_mcq_options = False
            html_lines.append(f'<div class="instruction">{line}</div>')
        elif re.match(r'^\([i|v|x|a-z|১-৯]+\)', line):
            if in_mcq_options:
                html_lines.append('</div></div>')
                in_mcq_options = False
            html_lines.append(f'<div class="question-item"><div class="q-text">{line}</div>')
            html_lines.append('<div class="mcq-options">')
            in_mcq_options = True
        elif re.match(r'^\([a-d]\)', line) and in_mcq_options:
            html_lines.append(f'<span class="option">{line}</span>')
        else:
            if in_mcq_options:
                html_lines.append('</div></div>')
                in_mcq_options = False
            html_lines.append(f'<p class="general-line">{line}</p>')

    if in_mcq_options:
        html_lines.append('</div></div>')

    content_html = "\n".join(html_lines)

    full_html = f"""<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CC-02 D.El.Ed Part-II Sample Question Paper</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Galada&family=Noto+Serif+Bengali:wght@400;600;700&family=Tiro+Bangla:ital@0;1&display=swap" rel="stylesheet">
    <style>
        @page {{
            size: A4;
            margin: 1.5cm;
        }}
        body {{
            font-family: 'Tiro Bangla', 'Noto Serif Bengali', serif;
            font-size: 14pt;
            line-height: 1.6;
            color: #111;
            background: #fff;
            margin: 0;
            padding: 20px;
        }}
        .paper-container {{
            max-width: 800px;
            margin: 0 auto;
            border: 2px solid #222;
            padding: 30px 40px;
            background: #fff;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }}
        .exam-header {{
            text-align: center;
            border-bottom: 2px double #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}
        .exam-header h1 {{
            font-size: 20pt;
            margin: 0 0 5px 0;
            font-weight: 700;
            color: #000;
        }}
        .exam-header h2 {{
            font-size: 16pt;
            margin: 0 0 5px 0;
            font-weight: 600;
        }}
        .exam-header h3 {{
            font-size: 15pt;
            margin: 0 0 10px 0;
            font-weight: 600;
            color: #1a2a3a;
        }}
        .meta-info {{
            font-size: 13pt;
            font-weight: 600;
            margin-top: 10px;
            display: flex;
            justify-content: space-between;
            border-top: 1px solid #ddd;
            padding-top: 8px;
        }}
        .group-header {{
            background: #f2f4f8;
            border-left: 4px solid #1a2a3a;
            padding: 6px 12px;
            font-size: 15pt;
            margin-top: 25px;
            margin-bottom: 12px;
            text-align: center;
        }}
        .instruction {{
            font-weight: 600;
            font-size: 13.5pt;
            margin-top: 15px;
            margin-bottom: 12px;
            background: #fafafa;
            padding: 6px 10px;
            border-radius: 4px;
        }}
        .question-item {{
            margin-bottom: 14px;
            page-break-inside: avoid;
        }}
        .q-text {{
            font-weight: 500;
            margin-bottom: 4px;
        }}
        .mcq-options {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 4px 15px;
            padding-left: 25px;
            margin-top: 4px;
            margin-bottom: 8px;
        }}
        .option {{
            font-size: 13pt;
            color: #222;
        }}
        .general-line {{
            margin: 8px 0;
            text-align: justify;
        }}
        @media print {{
            body {{
                padding: 0;
            }}
            .paper-container {{
                border: none;
                box-shadow: none;
                padding: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="paper-container">
        {content_html}
    </div>
</body>
</html>"""
    return full_html

def convert_to_pdf_headless(html_path, pdf_path):
    print(f"[*] Generating PDF via Firefox headless...")
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
        print(f"[OK] PDF saved: {pdf_path} ({len(pdf_data)//1024} KB)")
        return True
    finally:
        driver.quit()

def main():
    if not os.path.exists(RAW_FILE):
        print(f"[!] Raw file not found: {RAW_FILE}")
        return

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        raw_content = f.read()

    print(f"[*] Processing raw paper ({len(raw_content)} chars)...")
    html_content = build_html(raw_content)

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[OK] HTML saved: {HTML_FILE}")

    convert_to_pdf_headless(HTML_FILE, PDF_FILE)
    print("\n[SUCCESS] Paper format & PDF generated!")

if __name__ == "__main__":
    main()
