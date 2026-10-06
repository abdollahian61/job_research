"""Validate editable source registry; no network requests or crawling."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


def host_of(url):
    parsed = urlparse(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port not in (None, 443)):
        raise ValueError("Source URLs must be HTTPS URLs without credentials.")
    return parsed.hostname.lower().rstrip(".")


def load_sources(path="config/sources.json"):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema_version") != 1:
        raise ValueError("Unsupported source configuration version.")
    seen = set()
    for collection in ("sources", "company_sources"):
        rows = config.get(collection)
        if not isinstance(rows, list):
            raise ValueError(f"{collection} must be a list.")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("Each source must be an object.")
            source_id = row.get("id")
            if not isinstance(source_id, str) or not source_id or source_id in seen:
                raise ValueError("Source IDs must be nonempty and unique.")
            seen.add(source_id)
            host_of(row["url"])
            for flag in ("enabled", "allow_subdomains"):
                if type(row.get(flag)) is not bool:
                    raise ValueError(f"{flag} must be a boolean.")
    return config


def is_allowed_url(url, config):
    try:
        candidate = host_of(url)
    except (ValueError, TypeError):
        return False
    for row in config["sources"] + config["company_sources"]:
        if not row["enabled"]:
            continue
        allowed = host_of(row["url"])
        if candidate == allowed or (
            row["allow_subdomains"] and candidate.endswith("." + allowed)
        ):
            return True
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/sources.json")
    args = parser.parse_args()
    config = load_sources(args.config)
    print(json.dumps({"valid": True, "enabled_sources": [
        row["id"] for row in config["sources"] + config["company_sources"]
        if row["enabled"]
    ]}, indent=2))
