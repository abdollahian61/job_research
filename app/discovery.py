"""Bounded Internet discovery and collection into a durable review queue."""
from .sources import is_allowed_url, host_of
from .web_fetch import fetch_page
from .job_parser import parse_jobs


class Discovery:
    def __init__(self, config, searcher, store, max_queries=6, max_pages=10,
                 fetcher=fetch_page):
        if max_queries < 1 or max_pages < 1:
            raise ValueError("Discovery limits must be positive.")
        self.config = config
        self.searcher = searcher
        self.store = store
        self.max_queries = max_queries
        self.max_pages = max_pages
        self.fetcher = fetcher

    def run(self):
        report = {"queries": 0, "pages": 0, "queued": 0, "duplicates": 0, "errors": []}
        jobs = []
        visited = set()
        for source in self.config["sources"] + self.config["company_sources"]:
            if not source["enabled"] or report["queries"] >= self.max_queries:
                continue
            query = ('site:' + host_of(source["url"]) +
                     ' (DevOps OR "Platform Engineer" OR "Site Reliability Engineer")' +
                     ' (senior OR staff OR principal) (visa OR relocation)')
            report["queries"] += 1
            try:
                results = self.searcher.search(query, count=5)
            except Exception as error:
                report["errors"].append({"source": source["id"], "stage": "search",
                                         "error": type(error).__name__})
                continue
            for result in results:
                if not isinstance(result, dict):
                    continue
                url = result.get("url", "")
                if (url in visited or not is_allowed_url(url, self.config)
                        or report["pages"] >= self.max_pages):
                    continue
                visited.add(url)
                report["pages"] += 1
                try:
                    final_url, html = self.fetcher(url, self.config)
                    if not is_allowed_url(final_url, self.config):
                        raise ValueError("Final URL outside whitelist.")
                    extracted = parse_jobs(final_url, html, result.get("title", ""))
                    for job in extracted:
                        key = self.store.put(job)
                        if self.store.status(key) != "pending":
                            report["duplicates"] += 1
                            continue
                        # Discovery never asserts migration eligibility or sends mail.
                        self.store.update(key, "review", "Discovered online; verify vacancy, CV fit, language, visa and relocation.")
                        jobs.append(job)
                        report["queued"] += 1
                except Exception as error:
                    report["errors"].append({"url": url, "stage": "fetch_parse",
                                             "error": type(error).__name__})
        return jobs, report
