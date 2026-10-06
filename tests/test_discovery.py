"""Offline integration checks for Internet discovery."""
import json
import tempfile
import unittest
from pathlib import Path
from app.discovery import Discovery
from app.storage import JobStore
from app.sources import load_sources
from app.web_fetch import WhitelistRedirects
from app.job_parser import parse_jobs
from urllib.request import Request


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = JobStore(str(Path(self.temp.name) / "jobs.db"))
        self.config = load_sources()
        self.url = "https://relocate.me/jobs/example"
        self.html = '<script type="application/ld+json">' + json.dumps({
            "@type": "JobPosting", "title": "Senior DevOps Engineer",
            "description": "<p>Kubernetes role</p>",
            "hiringOrganization": {"name": "Test Company"},
            "jobLocation": {"address": {"addressCountry": "NL"}},
        }) + "</script>"

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_online_intake_queue_and_duplicates(self):
        url = self.url
        class Search:
            def search(self, query, count):
                return [{"url": url, "title": "Senior DevOps Engineer"},
                        {"url": "https://evil.example/job", "title": "Outside"}]
        fetched = []
        def fetch(url, config):
            fetched.append(url)
            return url, self.html
        discovery = Discovery(self.config, Search(), self.store,
                              max_queries=1, max_pages=1, fetcher=fetch)
        jobs, report = discovery.run()
        self.assertEqual(report["queued"], 1)
        self.assertEqual(fetched, [url])
        self.assertEqual(jobs[0]["country"], "Netherlands")
        self.assertIsNone(jobs[0]["visa_sponsorship"])
        key = self.store.put(jobs[0])
        self.assertEqual(self.store.status(key), "review")
        jobs, report = discovery.run()
        self.assertEqual(jobs, [])
        self.assertEqual(report["duplicates"], 1)

    def test_redirect_rejected_before_request(self):
        handler = WhitelistRedirects(self.config)
        with self.assertRaises(ValueError):
            handler.redirect_request(Request(self.url), None, 302, "Found", {},
                                     "https://evil.example/job")

    def test_nonstructured_page_remains_unverified(self):
        result = parse_jobs(self.url, "<html><p>Job listing</p></html>", "Search title")
        self.assertEqual(result[0]["source_kind"], "unverified_page_candidate")
        self.assertIsNone(result[0]["relocation_support"])

    def test_fetch_errors_reported_without_approval(self):
        url = self.url
        class Search:
            def search(self, query, count):
                return [{"url": url}]
        def fail(url, config):
            raise TimeoutError()
        jobs, report = Discovery(self.config, Search(), self.store,
                                 max_queries=1, fetcher=fail).run()
        self.assertEqual(jobs, [])
        self.assertEqual(report["errors"][0]["error"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
