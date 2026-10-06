"""Fetch only whitelisted HTTPS pages, including redirect destinations."""
from urllib.request import Request, HTTPRedirectHandler, build_opener
from .sources import is_allowed_url


class WhitelistRedirects(HTTPRedirectHandler):
    def __init__(self, config):
        self.config = config

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_allowed_url(newurl, self.config):
            raise ValueError("Redirect destination is outside whitelist.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url, config, timeout=30):
    if not is_allowed_url(url, config):
        raise ValueError("Page is outside whitelist.")
    opener = build_opener(WhitelistRedirects(config))
    request = Request(url, headers={"User-Agent": "JobResearch/0.1",
                                   "Accept": "text/html,application/xhtml+xml"})
    with opener.open(request, timeout=timeout) as response:
        if not is_allowed_url(response.geturl(), config):
            raise ValueError("Final page URL is outside whitelist.")
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError("Expected HTML job page.")
        raw = response.read(2_000_001)
        charset = response.headers.get_content_charset() or "utf-8"
        final_url = response.geturl()
    if len(raw) > 2_000_000:
        raise ValueError("Page exceeds size limit.")
    return final_url, raw.decode(charset, errors="replace")
