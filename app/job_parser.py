"""Extract schema.org JobPosting data; retain other pages as review candidates."""
import json
from datetime import datetime, timezone
from html.parser import HTMLParser


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self.text = []
        self.links = []
        self._script = None
        self._hidden = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self._hidden += 1
            if attrs.get("type", "").lower() == "application/ld+json":
                self._script = []
        elif tag == "style":
            self._hidden += 1
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "script":
            if self._script is not None:
                self.scripts.append("".join(self._script))
                self._script = None
            self._hidden = max(0, self._hidden - 1)
        elif tag == "style":
            self._hidden = max(0, self._hidden - 1)

    def handle_data(self, data):
        if self._script is not None:
            self._script.append(data)
        elif not self._hidden and data.strip():
            self.text.append(data.strip())


def plain_text(html):
    parser = PageParser()
    parser.feed(str(html or ""))
    return " ".join(parser.text)


def job_nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from job_nodes(item)
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if "JobPosting" in types:
            yield value
        for nested in value.values():
            if isinstance(nested, (list, dict)):
                yield from job_nodes(nested)


COUNTRIES = {"NL": "Netherlands", "DE": "Germany", "ES": "Spain",
             "PT": "Portugal", "BE": "Belgium", "LU": "Luxembourg",
             "AE": "United Arab Emirates", "SA": "Saudi Arabia",
             "QA": "Qatar", "OM": "Oman", "BH": "Bahrain", "KW": "Kuwait"}


def parse_jobs(url, html, search_title=""):
    parser = PageParser()
    parser.feed(html)
    nodes = []
    for script in parser.scripts:
        try:
            nodes.extend(job_nodes(json.loads(script)))
        except (ValueError, TypeError):
            continue
    collected_at = datetime.now(timezone.utc).isoformat()
    jobs = []
    for node in nodes:
        organization = node.get("hiringOrganization", {})
        location = node.get("jobLocation", {})
        if isinstance(location, list):
            location = location[0] if location else {}
        address = location.get("address", {}) if isinstance(location, dict) else {}
        country = address.get("addressCountry", "") if isinstance(address, dict) else ""
        if isinstance(country, dict):
            country = country.get("name", "")
        identifier = node.get("identifier")
        if isinstance(identifier, dict):
            identifier = identifier.get("value")
        job = {
            "url": url, "title": str(node.get("title", node.get("name", search_title))),
            "company": organization.get("name", "") if isinstance(organization, dict) else str(organization),
            "country": COUNTRIES.get(str(country).upper(), country),
            "description": plain_text(node.get("description", "")),
            "date_posted": node.get("datePosted"),
            "valid_through": node.get("validThrough"),
            "source_kind": "schema_jobposting", "collected_at": collected_at,
            "english_working_language": None,
            "visa_sponsorship": None, "relocation_support": None,
        }
        if identifier is not None and str(identifier).strip():
            job["id"] = str(identifier)
        jobs.append(job)
    if not jobs:
        jobs.append({
            "url": url, "title": search_title, "company": "", "country": "",
            "description": " ".join(parser.text)[:30000],
            "source_kind": "unverified_page_candidate", "collected_at": collected_at,
            "english_working_language": None,
            "visa_sponsorship": None, "relocation_support": None,
        })
    return jobs
