"""Deterministic initial filters; ambiguous migration conditions need review."""
import re
from .sources import is_allowed_url


def assess(job, config):
    if not is_allowed_url(job.get("url", ""), config):
        return "rejected", "Job URL is outside the configured whitelist."
    title = job.get("title", "")
    if not isinstance(title, str):
        return "rejected", "Invalid title."
    if re.search(r"\b(manager|director|head|intern|junior)\b", title, re.I):
        return "rejected", "Role is outside the senior technical target."
    if not re.search(r"\b(devops|platform|site reliability|sre|infrastructure)\b", title, re.I):
        return "rejected", "Role is outside the technical target."
    if not re.search(r"\b(senior|sr\.?|staff|principal)\b", title, re.I):
        return "review", "Seniority needs review."
    if job.get("country") not in config["target_countries"]:
        return "review", "Country is outside the default targets."
    if job.get("english_working_language") is not True:
        return "review", "English working language needs verification."
    for field in ("visa_sponsorship", "relocation_support"):
        if job.get(field) is False:
            return "rejected", f"{field} is explicitly unavailable."
        evidence = job.get(field + "_evidence")
        if (job.get(field) is not True or not isinstance(evidence, dict)
                or not evidence.get("quote")
                or not is_allowed_url(evidence.get("url", ""), config)):
            return "review", f"{field} needs sourced evidence."
    if not isinstance(job.get("description"), str) or not job["description"].strip():
        return "review", "Job description is missing."
    return "eligible", "Initial filters passed; eligibility evidence supplied by intake."
