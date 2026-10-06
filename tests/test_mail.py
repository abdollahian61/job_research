"""Offline checks for sending and reservations; never contacts SMTP."""
import tempfile
import unittest
import os
from unittest.mock import patch
from dataclasses import replace
from pathlib import Path
from app.mail_settings import MailSettings
from app.mail_ledger import MailLedger
from app.mailer import send_draft
from app.sources import load_sources


class MailTests(unittest.TestCase):
    def test_gmail_requires_only_email_and_app_password(self):
        with patch.dict(os.environ, {"SMTP_USERNAME": "me@gmail.com",
                                    "SMTP_PASSWORD": "abcd efgh ijkl mnop",
                                    "SEND_EMAILS": "true"}, clear=True):
            settings = MailSettings.from_env()
        self.assertEqual((settings.host, settings.port, settings.tls_mode),
                         ("smtp.gmail.com", 587, "starttls"))
        self.assertEqual(settings.sender, "me@gmail.com")
        self.assertEqual(settings.password, "abcdefghijklmnop")
        self.assertTrue(settings.enabled)

    def test_old_blank_host_and_sender_use_gmail_defaults(self):
        with patch.dict(os.environ, {"SMTP_HOST": "", "SMTP_FROM": "",
                                    "SMTP_USERNAME": "me@gmail.com"}, clear=True):
            settings = MailSettings.from_env()
        self.assertEqual(settings.host, "smtp.gmail.com")
        self.assertEqual(settings.sender, "me@gmail.com")
        self.assertFalse(settings.enabled)

    def test_other_provider_overrides_are_preserved(self):
        with patch.dict(os.environ, {"SMTP_HOST": "smtp.example.com", "SMTP_PORT": "465",
                                    "SMTP_TLS_MODE": "ssl", "SMTP_USERNAME": "login",
                                    "SMTP_PASSWORD": "keep spaces", "SMTP_FROM": "me@example.com",
                                    "SEND_EMAILS": "true"}, clear=True):
            settings = MailSettings.from_env()
        self.assertEqual(settings.password, "keep spaces")
        self.assertEqual((settings.host, settings.port, settings.sender),
                         ("smtp.example.com", 465, "me@example.com"))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "jobs.db")
        self.resume = Path(self.tmp.name) / "cv.pdf"
        self.resume.write_bytes(b"%PDF-1.4\nTest fixture, not a real CV.")
        self.ledger = MailLedger(self.path)
        self.settings = MailSettings("smtp.example.com", 587, "test", "test",
                                     "me@example.com", "starttls", 5, True)
        self.sources = load_sources()
        self.recipient = {"email": "hiring@example.com", "verified": True,
                          "purpose": "job_application",
                          "source_url": "https://relocate.me/jobs/example",
                          "source_evidence": "Apply: hiring@example.com"}
        self.draft = {"subject": "Application", "body": "Test draft"}

    def tearDown(self):
        self.ledger.close()
        self.tmp.cleanup()

    def run_send(self, key="job1", transport=lambda *args: None, **kwargs):
        return send_draft(self.settings, self.ledger, self.sources, key,
                          self.recipient, self.draft, self.resume,
                          transport=transport, **kwargs)

    def test_send_and_duplicate_block(self):
        calls = []
        result = self.run_send(transport=lambda s, m: calls.append(m))
        self.assertEqual(result["status"], "sent")
        self.assertEqual(len(list(calls[0].iter_attachments())), 1)
        with self.assertRaises(ValueError):
            self.run_send(transport=lambda *a: self.fail("Duplicate send"))
        self.assertEqual(len(calls), 1)

    def test_daily_limit_shared_between_connections(self):
        self.ledger.reserve("first", "x@example.com", "<first>", 1)
        second = MailLedger(self.path)
        try:
            with self.assertRaises(ValueError):
                second.reserve("second", "y@example.com", "<second>", 1)
        finally:
            second.close()

    def test_uncertain_send_is_not_retried(self):
        def timeout(*args):
            raise TimeoutError()
        with self.assertRaises(TimeoutError):
            self.run_send(transport=timeout)
        self.assertEqual(self.ledger.db.execute(
            "SELECT status FROM email_sends").fetchone()[0], "uncertain")
        with self.assertRaises(ValueError):
            self.run_send()

    def test_dry_run_does_not_send_or_reserve(self):
        self.settings = replace(self.settings, enabled=False)
        result = self.run_send(transport=lambda *a: self.fail("Dry run sent mail"))
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(self.ledger.db.execute(
            "SELECT COUNT(*) FROM email_sends").fetchone()[0], 0)

    def test_unverified_recipient_is_blocked(self):
        self.recipient["verified"] = False
        with self.assertRaises(ValueError):
            self.run_send()

    def test_test_mail_can_only_target_sender(self):
        with self.assertRaises(ValueError):
            self.run_send(test_to="other@example.com")
        self.assertEqual(self.run_send(test_to="me@example.com")["status"], "sent")


if __name__ == "__main__":
    unittest.main()
