import os
import sqlite3
import json
import uuid
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        # Ensure the directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Quotes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quotes (
                    quote_id TEXT PRIMARY KEY,
                    quote_text TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    author_url TEXT,
                    tags_json TEXT,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    pages_scraped INTEGER,
                    quotes_seen INTEGER,
                    status TEXT,
                    error TEXT
                )
            ''')
            
            # Quote observations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS quote_observations (
                    run_id TEXT,
                    quote_id TEXT,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id),
                    FOREIGN KEY(quote_id) REFERENCES quotes(quote_id),
                    PRIMARY KEY(run_id, quote_id)
                )
            ''')
            conn.commit()

    def start_run(self):
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, started_at, status) VALUES (?, ?, ?)",
                (run_id, started_at, 'running')
            )
            conn.commit()
        return run_id

    def finish_run(self, run_id, pages_scraped, quotes_seen, status='success', error=None):
        finished_at = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE runs SET finished_at = ?, pages_scraped = ?, quotes_seen = ?, status = ?, error = ? WHERE run_id = ?",
                (finished_at, pages_scraped, quotes_seen, status, error, run_id)
            )
            conn.commit()

    def get_quote(self, quote_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM quotes WHERE quote_id = ?", (quote_id,))
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            return None

    def upsert_quote(self, quote_data):
        quote_id = quote_data['quote_id']
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            existing = self.get_quote(quote_id)
            if existing:
                # Update last_seen_at and tags if they changed
                # The user said: "Update" for tag changes
                conn.execute(
                    "UPDATE quotes SET last_seen_at = ?, tags_json = ?, author_url = ? WHERE quote_id = ?",
                    (now, quote_data['tags_json'], quote_data['author_url'], quote_id)
                )
                return 'updated' if existing['tags_json'] != quote_data['tags_json'] else 'seen'
            else:
                conn.execute(
                    "INSERT INTO quotes (quote_id, quote_text, author_name, author_url, tags_json, first_seen_at, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (quote_id, quote_data['quote_text'], quote_data['author_name'], quote_data['author_url'], quote_data['tags_json'], now, now)
                )
                return 'new'

    def record_observation(self, run_id, quote_id):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO quote_observations (run_id, quote_id) VALUES (?, ?)",
                (run_id, quote_id)
            )
            conn.commit()

    def get_last_run(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
            return None

    def get_quotes_from_run(self, run_id):
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT q.* FROM quotes q
                JOIN quote_observations o ON q.quote_id = o.quote_id
                WHERE o.run_id = ?
            ''', (run_id,))
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_previous_run_id(self, current_run_id):
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT run_id FROM runs 
                WHERE started_at < (SELECT started_at FROM runs WHERE run_id = ?)
                AND status = 'success'
                ORDER BY started_at DESC LIMIT 1
            ''', (current_run_id,))
            row = cursor.fetchone()
            return row[0] if row else None
            
    def get_all_quotes(self):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM quotes")
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
