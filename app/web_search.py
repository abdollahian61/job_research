"""Replaceable search adapter. First provider: Brave Web Search API."""
import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class BraveSearch:
    def __init__(self, api_key=None, timeout=30):
        self.api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("Set BRAVE_SEARCH_API_KEY in .env before live search.")

    def search(self, query, count=5):
        query_string = urlencode({"q": query, "count": min(max(count, 1), 20)})
        request = Request("https://api.search.brave.com/res/v1/web/search?" + query_string,
                          headers={"X-Subscription-Token": self.api_key,
                                   "Accept": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Search response exceeds size limit.")
        return json.loads(raw).get("web", {}).get("results", [])
