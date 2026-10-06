"""Transactional send reservations; uncertain sends are never auto-retried."""
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path


class MailLedger:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=30)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS email_sends(
                job_key TEXT PRIMARY KEY, recipient TEXT NOT NULL,
                local_day TEXT NOT NULL, status TEXT NOT NULL, message_id TEXT NOT NULL
            )
        """)
        self.db.commit()

    def reserve(self, job_key, recipient, message_id, daily_limit):
        day = datetime.now(ZoneInfo("Asia/Tehran")).date().isoformat()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute("SELECT 1 FROM email_sends WHERE job_key=?", (job_key,)).fetchone():
                raise ValueError("This job already has a send reservation; check its status.")
            count = self.db.execute("SELECT COUNT(*) FROM email_sends WHERE local_day=?", (day,)).fetchone()[0]
            if count >= daily_limit:
                raise ValueError("Daily email limit reached.")
            self.db.execute("INSERT INTO email_sends VALUES(?,?,?,'sending',?)",
                            (job_key, recipient, day, message_id))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def finish(self, job_key, status):
        if status not in {"sent", "uncertain"}:
            raise ValueError("Invalid send status.")
        with self.db:
            self.db.execute("UPDATE email_sends SET status=? WHERE job_key=?", (status, job_key))

    def close(self):
        self.db.close()
