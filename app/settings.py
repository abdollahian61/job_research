"""Model settings loaded from environment."""
import os
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse


def load_env(path=".env"):
    """Load simple KEY=value lines without overriding process environment."""
    source = Path(path)
    if not source.exists():
        return
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not key.strip().isidentifier():
            raise ValueError(f"Invalid environment setting on line {number}")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


@dataclass(frozen=True)
class ModelSettings:
    base_url: str
    model: str
    api_key: str = ""
    timeout: int = 120
    max_tokens: int = 800

    @classmethod
    def from_env(cls):
        base_url = os.getenv("LLM_BASE_URL", "").strip().rstrip("/")
        model = os.getenv("LLM_MODEL", "").strip()
        parsed = urlparse(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or "YOUR_" in base_url or not model or "YOUR_" in model):
            raise ValueError("Set LLM_BASE_URL and LLM_MODEL to real values.")
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "120"))
        max_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "800"))
        if timeout <= 0 or max_tokens <= 0:
            raise ValueError("Timeout and token limit must be positive.")
        return cls(base_url, model, os.getenv("LLM_API_KEY", ""), timeout, max_tokens)


