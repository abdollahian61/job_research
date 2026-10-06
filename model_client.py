"""Compatibility CLI for the modular model adapter."""
import json
from pathlib import Path
from app.settings import load_env, ModelSettings
from app.llm import generate_email

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--job", required=True)
    args = parser.parse_args()
    load_env()
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    job = Path(args.job).read_text(encoding="utf-8")
    print(json.dumps(generate_email(ModelSettings.from_env(), profile, job), ensure_ascii=False, indent=2))
