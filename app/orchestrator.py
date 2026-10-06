"""Coordinate intake, filtering, drafting and durable state."""
from .filtering import assess
from .llm import generate_email


class Orchestrator:
    def __init__(self, sources, model_settings, store, draft_limit=5, generator=generate_email):
        if draft_limit < 1:
            raise ValueError("Draft limit must be positive.")
        self.sources = sources
        self.model_settings = model_settings
        self.store = store
        self.draft_limit = draft_limit
        self.generator = generator

    def run(self, jobs, profile):
        report = []
        drafted = 0
        for job in jobs:
            key = self.store.put(job)
            previous = self.store.status(key)
            if previous in {"drafted", "rejected", "review"}:
                report.append({"key": key, "status": "skipped", "reason": "Already processed."})
                continue
            status, reason = assess(job, self.sources)
            if status != "eligible":
                self.store.update(key, status, reason)
            elif drafted >= self.draft_limit:
                status, reason = "pending", "Per-run draft limit reached."
                self.store.update(key, status, reason)
            else:
                try:
                    draft = self.generator(self.model_settings, profile, job["description"])
                except Exception as error:
                    # Keep pending on network/model failure; do not change providers.
                    status, reason = "pending", "Draft failed: " + type(error).__name__
                    self.store.update(key, status, reason)
                else:
                    status, reason = "drafted", "Draft stored; no email sent."
                    self.store.update(key, status, reason, draft)
                    drafted += 1
            report.append({"key": key, "status": status, "reason": reason})
        return report
