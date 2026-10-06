"""Read private chat IDs from recent bot messages without printing the token."""
import json
import os
from urllib.request import Request, urlopen
from app.settings import load_env

if __name__ == "__main__":
    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env.")
    try:
        request = Request("https://api.telegram.org/bot" + token + "/getUpdates")
        with urlopen(request, timeout=15) as response:
            result = json.loads(response.read(1_000_000))
        if not result.get("ok"):
            raise ValueError("Bot request failed.")
        ids = sorted({item["message"]["chat"]["id"] for item in result.get("result", [])
                      if item.get("message", {}).get("chat", {}).get("type") == "private"})
        print(json.dumps({"private_chat_ids": ids}))
        if not ids:
            print("Open your bot and send /start, then run again.")
    except Exception as error:
        raise SystemExit("Could not retrieve chat IDs: " + type(error).__name__) from None
