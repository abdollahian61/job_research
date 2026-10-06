"""Durable job status and drafts. Does not send email."""
import hashlib
import json
import sqlite3
from pathlib import Path


class JobStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_key TEXT PRIMARY KEY, payload TEXT NOT NULL,
                status TEXT NOT NULL, reason TEXT NOT NULL DEFAULT '',
                draft TEXT
            )
        """)
        self.db.commit()

    def put(self, job):
        # Prefer company + stable posting ID; URL fallback.
        identity = (str(job.get("company", "")).strip().lower() + ":" +
                    str(job["id"])) if job.get("id") else str(job.get("url", ""))
        if not identity:
            raise ValueError("Job requires an ID or URL.")
        key = hashlib.sha256(identity.encode()).hexdigest()
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO jobs(job_key,payload,status) VALUES(?,?,'pending')",
                            (key, json.dumps(job, ensure_ascii=False)))
        return key

    def status(self, key):
        return self.db.execute("SELECT status FROM jobs WHERE job_key=?", (key,)).fetchone()[0]

    def update(self, key, status, reason, draft=None):
        with self.db:
            self.db.execute("UPDATE jobs SET status=?,reason=?,draft=? WHERE job_key=?",
                            (status, reason, json.dumps(draft, ensure_ascii=False) if draft else None, key))

    def close(self):
        self.db.close()
