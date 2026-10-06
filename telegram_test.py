"""Send a Telegram connectivity test to the configured chat."""
from app.settings import load_env
from app.notifications import notify

if __name__ == "__main__":
    load_env()
    if not notify("connection test", {"message": "Telegram notifications are ready."}):
        raise SystemExit("Telegram test failed or notifications are disabled.")
    print("Telegram test delivered.")
