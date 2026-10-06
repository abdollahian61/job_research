"""Search allowed sites and store candidates for review; no model or mail calls."""
import argparse
import json
import os
from pathlib import Path
from app.settings import load_env
from app.sources import load_sources
from app.storage import JobStore
from app.web_search import BraveSearch
from app.discovery import Discovery

from app.notifications import action, notify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", default="config/sources.json")
    parser.add_argument("--database", default="data/jobs.sqlite3")
    parser.add_argument("--output", default="data/discovered_jobs.json")
    args = parser.parse_args()
    load_env()
    with action("discover_jobs"):
        config = load_sources(args.sources)
        search_provider = os.getenv("SEARCH_PROVIDER", "brave")
        if search_provider != "brave":
            raise ValueError("Only brave is implemented; other providers need an adapter.")
        searcher = BraveSearch()
        store = JobStore(args.database)
        try:
            jobs, report = Discovery(
                config, searcher, store,
                max_queries=int(os.getenv("SEARCH_MAX_QUERIES_PER_RUN", "6")),
                max_pages=int(os.getenv("SEARCH_MAX_PAGES_PER_RUN", "10")),
            ).run()
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            # Per-run export; all collected candidates persist in SQLite.
            output.write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
            notify("discovery: results", report)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        finally:
            store.close()
