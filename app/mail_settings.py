"""SMTP settings from .env; real sending is explicitly enabled."""
import os
import re
from dataclasses import dataclass


def valid_email(value):
    return isinstance(value, str) and bool(re.fullmatch(
        r"[A-Za-z0-9.!#$%&'*+/=?^_\x60{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}", value))


@dataclass(frozen=True)
class MailSettings:
    host: str
    port: int
    username: str
    password: str
    sender: str
    tls_mode: str
    daily_limit: int
    enabled: bool

    @classmethod
    def from_env(cls):
        settings = cls(
            os.getenv("SMTP_HOST", ""), int(os.getenv("SMTP_PORT", "587")),
            os.getenv("SMTP_USERNAME", ""), os.getenv("SMTP_PASSWORD", ""),
            os.getenv("SMTP_FROM", ""), os.getenv("SMTP_TLS_MODE", "starttls"),
            int(os.getenv("DAILY_EMAIL_LIMIT", "5")),
            os.getenv("SEND_EMAILS", "false").lower() == "true",
        )
        if not valid_email(settings.sender):
            raise ValueError("Set SMTP_FROM to a valid email address.")
        if settings.daily_limit < 1 or not 1 <= settings.port <= 65535:
            raise ValueError("Invalid SMTP port or daily limit.")
        if settings.tls_mode not in {"starttls", "ssl"}:
            raise ValueError("SMTP_TLS_MODE must be starttls or ssl.")
        if settings.enabled and (not settings.host or not settings.username or not settings.password):
            raise ValueError("SMTP credentials are required for sending.")
        return settings
