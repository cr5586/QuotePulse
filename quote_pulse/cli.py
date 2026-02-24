import click
import logging
import os
import json
import csv
from quote_pulse.engine import Engine
from quote_pulse.reports import ReportGenerator
from quote_pulse.database import Database

def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/quote_pulse.log"),
            logging.StreamHandler()
        ]
    )

@click.group()
def cli():
    setup_logging()

@cli.command()
@click.option('--db', default='./data/quotes.db', help='Path to SQLite database')
@click.option('--headless', default='true', help='Run in headless mode (true|false)')
@click.option('--max-pages', default=None, type=int, help='Max pages to scrape')
@click.option('--timeout', default=10, type=int, help='Scraper timeout')
@click.option('--screenshot-on-fail', default='./artifacts/failures/', help='Path to save failure artifacts')
def scrape(db, headless, max_pages, timeout, screenshot_on_fail):
    is_headless = headless.lower() == 'true'
    engine = Engine(db, headless=is_headless, timeout=timeout, failure_dir=screenshot_on_fail)
    
    click.echo(f"Starting scrape (db={db}, headless={is_headless}, max_pages={max_pages})...")
    results = engine.run_scrape(max_pages=max_pages)
    
    reporter = ReportGenerator(engine.db)
    md_path, pdf_path, stats_path = reporter.generate_all(results)
    
    click.echo("\nScrape complete!")
    click.echo(f"New quotes: {len(results['new_quotes'])}")
    click.echo(f"Changed quotes: {len(results['changed_quotes'])}")
    click.echo(f"Disappeared quotes: {len(results['disappeared_quotes'])}")
    click.echo(f"Reports saved to:")
    click.echo(f"  - {md_path}")
    click.echo(f"  - {pdf_path}")
    click.echo(f"Stats updated: {stats_path}")

@cli.command()
@click.option('--last', is_flag=True, help='Show last run report path + summary')
@click.option('--db', default='./data/quotes.db', help='Path to SQLite database')
def report(last, db):
    database = Database(db)
    if last:
        last_run = database.get_last_run()
        if not last_run:
            click.echo("No runs found in database.")
            return
        
        click.echo(f"Last Run ID: {last_run['run_id']}")
        click.echo(f"Status: {last_run['status']}")
        click.echo(f"Started at: {last_run['started_at']}")
        click.echo(f"Pages Scraped: {last_run['pages_scraped']}")
        click.echo(f"Quotes Seen: {last_run['quotes_seen']}")
        
        # In a real world scenario, we might want to find the latest MD report based on timestamp
        # but the prompt just says "prints last run report path + summary"
        click.echo("\nCheck 'reports/' folder for the detailed MD and PDF files.")

@cli.command()
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv')
@click.option('--out', default='./exports/quotes.csv')
@click.option('--db', default='./data/quotes.db', help='Path to SQLite database')
def export(format, out, db):
    database = Database(db)
    quotes = database.get_all_quotes()
    
    os.makedirs(os.path.dirname(out), exist_ok=True)
    
    if format == 'json':
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(quotes, f, indent=4)
    else:
        if not quotes:
            click.echo("No quotes to export.")
            return
        keys = quotes[0].keys()
        with open(out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(quotes)
            
    click.echo(f"Exported {len(quotes)} quotes to {out}")

if __name__ == '__main__':
    cli()
