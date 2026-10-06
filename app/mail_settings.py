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
        host = os.getenv("SMTP_HOST", "").strip() or "smtp.gmail.com"
        username = os.getenv("SMTP_USERNAME", "").strip()
        password = os.getenv("SMTP_PASSWORD", "")
        # Google displays App Passwords in groups; pasted spaces are not part of it.
        if host.lower() == "smtp.gmail.com":
            password = password.replace(" ", "")
        settings = cls(
            host, int(os.getenv("SMTP_PORT", "").strip() or "587"),
            username, password,
            os.getenv("SMTP_FROM", "").strip() or username,
            os.getenv("SMTP_TLS_MODE", "").strip() or "starttls",
            int(os.getenv("DAILY_EMAIL_LIMIT", "5")),
            os.getenv("SEND_EMAILS", "false").lower() == "true",
        )
        if not valid_email(settings.sender):
            raise ValueError("Set SMTP_USERNAME to your Gmail address (or override SMTP_FROM).")
        if settings.daily_limit < 1 or not 1 <= settings.port <= 65535:
            raise ValueError("Invalid SMTP port or daily limit.")
        if settings.tls_mode not in {"starttls", "ssl"}:
            raise ValueError("SMTP_TLS_MODE must be starttls or ssl.")
        if settings.enabled and (not settings.host or not settings.username or not settings.password):
            raise ValueError("SMTP credentials are required for sending.")
        return settings
