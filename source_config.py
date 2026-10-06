"""Compatibility CLI for editable source registry."""
import argparse
import json
from app.sources import load_sources, is_allowed_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/sources.json")
    args = parser.parse_args()
    config = load_sources(args.config)
    print(json.dumps({"valid": True, "enabled_sources": [
        row["id"] for row in config["sources"] + config["company_sources"]
        if row["enabled"]
    ]}, indent=2))
