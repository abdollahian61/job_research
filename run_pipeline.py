"""Run the modular draft pipeline on a normalized jobs file."""
import argparse
import json
from pathlib import Path
from app.settings import load_env, ModelSettings
from app.sources import load_sources
from app.intake import read_jobs
from app.storage import JobStore
from app.orchestrator import Orchestrator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--sources", default="config/sources.json")
    parser.add_argument("--database", default="data/jobs.sqlite3")
    parser.add_argument("--draft-limit", type=int, default=5)
    args = parser.parse_args()
    load_env()
    settings = ModelSettings.from_env()
    sources = load_sources(args.sources)
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    if not isinstance(profile, dict) or not profile:
        raise ValueError("Profile must be a nonempty object with verified CV facts.")
    store = JobStore(args.database)
    try:
        report = Orchestrator(sources, settings, store, args.draft_limit).run(read_jobs(args.jobs), profile)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        store.close()
