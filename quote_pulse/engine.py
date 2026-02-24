import json
import logging
from datetime import datetime
from quote_pulse.database import Database
from quote_pulse.scraper import Scraper

logger = logging.getLogger(__name__)

class Engine:
    def __init__(self, db_path, headless=True, timeout=10, failure_dir='./artifacts/failures/'):
        self.db = Database(db_path)
        self.scraper = Scraper(headless=headless, timeout=timeout, failure_dir=failure_dir)

    def run_scrape(self, max_pages=None):
        run_id = self.db.start_run()
        logger.info(f"Starting run {run_id}")
        
        try:
            quotes, pages_scraped = self.scraper.scrape(max_pages=max_pages, run_id=run_id)
            
            new_quotes = []
            changed_quotes = []
            seen_quote_ids = set()
            
            for q in quotes:
                quote_data = {
                    "quote_id": q["quote_id"],
                    "quote_text": q["quote_text"],
                    "author_name": q["author_name"],
                    "author_url": q["author_url"],
                    "tags_json": json.dumps(q["tags"]),
                }
                
                status = self.db.upsert_quote(quote_data)
                self.db.record_observation(run_id, q["quote_id"])
                seen_quote_ids.add(q["quote_id"])
                
                if status == 'new':
                    new_quotes.append(q)
                elif status == 'updated':
                    changed_quotes.append(q)

            # Detect disappeared quotes
            disappeared_quotes = []
            prev_run_id = self.db.get_previous_run_id(run_id)
            if prev_run_id:
                prev_quotes = self.db.get_quotes_from_run(prev_run_id)
                prev_ids = {pq['quote_id'] for pq in prev_quotes}
                disappeared_ids = prev_ids - seen_quote_ids
                
                # Fetch disappeared quote details from DB
                for d_id in disappeared_ids:
                    d_quote = self.db.get_quote(d_id)
                    if d_quote:
                        disappeared_quotes.append(d_quote)

            self.db.finish_run(run_id, pages_scraped, len(seen_quote_ids), status='success')
            
            return {
                "run_id": run_id,
                "new_quotes": new_quotes,
                "changed_quotes": changed_quotes,
                "disappeared_quotes": disappeared_quotes,
                "total_seen": len(seen_quote_ids),
                "pages_scraped": pages_scraped
            }

        except Exception as e:
            logger.error(f"Run {run_id} failed: {e}", exc_info=True)
            self.db.finish_run(run_id, 0, 0, status='fail', error=str(e))
            raise
