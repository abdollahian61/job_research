"""Read normalized jobs from JSON. Live source adapters are not yet implemented."""
import json
from pathlib import Path


def read_jobs(path):
    jobs = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs):
        raise ValueError("Jobs file must contain a list of objects.")
    return jobs
