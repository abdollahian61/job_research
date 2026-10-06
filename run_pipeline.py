"""Run the modular draft pipeline on a normalized jobs file."""
import argparse
import json
from pathlib import Path
from app.settings import load_env, ModelSettings
from app.sources import load_sources
from app.intake import read_jobs
from app.storage import JobStore
from app.orchestrator import Orchestrator
from app.resume import load_candidate_profile

from app.notifications import action, notify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", required=True)
    candidate = parser.add_mutually_exclusive_group()
    candidate.add_argument("--profile", help="Optional verified JSON profile instead of PDF")
    candidate.add_argument("--resume", help="PDF path; defaults to RESUME_PATH or resume.pdf")
    parser.add_argument("--sources", default="config/sources.json")
    parser.add_argument("--database", default="data/jobs.sqlite3")
    parser.add_argument("--draft-limit", type=int, default=5)
    args = parser.parse_args()
    load_env()
    with action("run_pipeline"):
        settings = ModelSettings.from_env()
        sources = load_sources(args.sources)
        profile = load_candidate_profile(args.profile, args.resume)
        store = JobStore(args.database)
        try:
            report = Orchestrator(sources, settings, store, args.draft_limit).run(read_jobs(args.jobs), profile)
            for item in report:
                notify("pipeline: job result", item)
            print(json.dumps(report, ensure_ascii=False, indent=2))
        finally:
            store.close()
