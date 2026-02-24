# QuotePulse — JS Quotes Scraper + Change Tracker

QuotePulse is a professional-grade web scraping tool designed to extract quotes from JS-rendered websites (specifically `quotes.toscrape.com/js`), store them in a local SQLite database, and track changes across different runs.

It's perfect for demonstrating data engineering basics like idempotent processing, change detection, and automated reporting.

## Features

- **Selenium-powered**: Handles JavaScript-rendered content with ease.
- **Change Tracking**: Automatically detects new quotes, disappeared quotes, and tag changes between runs.
- **SQLite Storage**: Maintains a persistent record of all quotes and scraping sessions.
- **Automated Reporting**: Generates beautiful **PDF** and **Markdown** reports after every scrape.
- **Data Analytics**: Exports high-level stats (top authors, tag distribution) to JSON and Markdown.
- **Failure Recovery**: Saves screenshots and HTML dumps if a scraping attempt fails.

## Prerequisites

- **Python 3.8+**
- **Google Chrome**: The scraper uses Chrome in headless mode by default.
  - **Fedora users**: You can install Chrome via: `sudo dnf install google-chrome-stable`

## Getting Started

### 0. Verify your Environment
Run the included check script to ensure you have everything needed:
```bash
python3 check_setup.py
```

### 1. Initialize the Environment

Clone the repository and install the required dependencies:

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Run your first Scrape

To start scraping the site, simply run:

```bash
python3 quote_pulse_cli.py scrape --max-pages 5
```

*This will scrape the first 5 pages, save the results to the database, and generate reports in the `reports/` folder.*

### 3. View Reports

After a run, check the following folders:
- `reports/`: Contains `run_<timestamp>.pdf` and `run_<timestamp>.md` with a summary of changes.
- `reports/summary.md`: A global overview of all scraped data.
- `exports/stats.json`: Detailed analytics on authors and tags.

## CLI Usage Guide

The `quote_pulse_cli.py` provides several commands:

### Scrape
Extract quotes and update the database.
```bash
python3 quote_pulse_cli.py scrape [OPTIONS]

Options:
  --db TEXT                  Path to SQLite database (default: ./data/quotes.db)
  --headless true|false      Run in headless mode (default: true)
  --max-pages INTEGER        Limit the number of pages to scrape
  --timeout INTEGER          Wait timeout for elements (default: 10s)
  --screenshot-on-fail PATH  Where to save failure artifacts
```

### Report
Get a quick summary of the last run.
```bash
python3 quote_pulse_cli.py report --last
```

### Export
Export all collected quotes to CSV or JSON.
```bash
python3 quote_pulse_cli.py export --format csv --out ./exports/my_quotes.csv
```

## Project Structure

- `quote_pulse/`: Core logic (scraper, engine, database, reporting).
- `data/`: SQLite database files.
- `reports/`: Generated PDF and Markdown reports.
- `exports/`: Data exports and analytics.
- `logs/`: Application logs.
- `artifacts/`: Screenshots and HTML dumps from failed runs.

## Technical Highlights

- **Dynamic Driver Management**: Uses Selenium 4's built-in manager to automatically download the correct WebDriver for your OS (Linux, Mac, or Windows).
- **Deterministic IDs**: Every quote is assigned a unique SHA-256 ID based on its text and author, ensuring consistent tracking even if URLs change.
- **Explicit Waits**: Uses Selenium's `WebDriverWait` for robustness against network latency.
- **Relational Schema**: Uses three tables (`quotes`, `runs`, `quote_observations`) to enable complex historical analysis.
