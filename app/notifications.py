"""Optional Telegram activity notifications. Failures do not repeat business actions."""
import json
import logging
import os
from contextlib import contextmanager
from urllib.request import Request, urlopen


def notify(event, details=None):
    if os.getenv("TELEGRAM_ENABLED", "false").lower() != "true":
        return False
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        logging.warning("Telegram settings are incomplete.")
        return False
    # Never include credentials, resume contents or SMTP passwords in notifications.
    safe_details = details or {}
    text = "Job Research | " + event + "\n" + json.dumps(safe_details, ensure_ascii=False)
    request = Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text[:4000]}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read(100000))
        if not result.get("ok"):
            logging.warning("Telegram rejected notification.")
            return False
        return True
    except Exception as error:
        # HTTP errors may contain the token-bearing URL; log only the exception class.
        logging.warning("Telegram notification failed: %s", type(error).__name__)
        return False


@contextmanager
def action(name):
    notify(name + ": started")
    try:
        yield
    except Exception as error:
        notify(name + ": failed", {"error": type(error).__name__})
        raise
    else:
        notify(name + ": completed")
