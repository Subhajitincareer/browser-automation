# Gemini Notebook Automation & Exam Paper Generator

Automated browser tool that interacts with Google Notebook LM / Gemini Notebook using Selenium and Firefox profile. It sends structured expert prompts, extracts generated responses, and formats them into beautiful HTML and PDF documents.

## Features
- **Browser Automation**: Uses existing logged-in Firefox profile via Selenium.
- **Clipboard Injection**: Pastes large prompts (5000+ chars) seamlessly without Angular validation lag.
- **Output Generation**: Transforms raw Bengali responses into styled A4 print-ready HTML & PDF exam papers.
- **Temp Storage Optimization**: Redirects temporary files to prevent disk space errors (`os error 112`).

## Project Structure
- `notebook_pipeline.py`: Full end-to-end pipeline (Notebook -> Extract -> Gemini API -> HTML -> PDF).
- `generate_final_outputs.py`: Fast offline formatter and PDF generator from raw extracted text.
- `notebook_automation.py`: Helper script for notebook creation, search, and deep research actions.
- `scrape_notebook.py`: Basic scraper script for Google Notebook.
- `html_to_pdf.py`: Firefox headless print-to-PDF utility.
- `cc02_prompt.txt`: Structured Bengali CC-02 D.El.Ed exam prompt.

## Usage

```bash
# 1. Install dependencies
pip install selenium beautifulsoup4 google-genai

# 2. Run offline HTML & PDF generator
python generate_final_outputs.py

# 3. Run full automated live pipeline
python notebook_pipeline.py --prompt-file cc02_prompt.txt --output-name cc02_sample_paper
```
