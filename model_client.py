"""Compatibility CLI for the modular model adapter."""
import json
from pathlib import Path
from app.settings import load_env, ModelSettings
from app.llm import generate_email
from app.resume import load_candidate_profile

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    candidate = parser.add_mutually_exclusive_group()
    candidate.add_argument("--profile", help="Optional verified JSON profile instead of PDF")
    candidate.add_argument("--resume", help="PDF path; defaults to RESUME_PATH or resume.pdf")
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    load_env()
    profile = load_candidate_profile(args.profile, args.resume)
    job = Path(args.job).read_text(encoding="utf-8")
    print(json.dumps(generate_email(ModelSettings.from_env(), profile, job), ensure_ascii=False, indent=2))
