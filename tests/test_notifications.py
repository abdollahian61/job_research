"""Offline Telegram tests; no external messages are sent."""
import json
import os
import unittest
from unittest.mock import patch
from app.notifications import notify, action


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, size): return b'{"ok":true}'


class NotificationTests(unittest.TestCase):
    def test_disabled_does_not_call_network(self):
        with patch.dict(os.environ, {"TELEGRAM_ENABLED": "false"}), patch("app.notifications.urlopen") as network:
            self.assertFalse(notify("test"))
            network.assert_not_called()

    def test_send_payload(self):
        with patch.dict(os.environ, {"TELEGRAM_ENABLED":"true",
                                     "TELEGRAM_BOT_TOKEN":"fake-token",
                                     "TELEGRAM_CHAT_ID":"123"}):
            with patch("app.notifications.urlopen", return_value=Response()) as network:
                self.assertTrue(notify("test", {"queued": 2}))
                request = network.call_args.args[0]
                payload = json.loads(request.data)
                self.assertEqual(payload["chat_id"], "123")
                self.assertIn('"queued": 2', payload["text"])
                self.assertNotIn("fake-token", payload["text"])

    def test_error_does_not_escape_or_expose_token(self):
        with patch.dict(os.environ, {"TELEGRAM_ENABLED":"true",
                                     "TELEGRAM_BOT_TOKEN":"secret-test",
                                     "TELEGRAM_CHAT_ID":"123"}):
            with patch("app.notifications.urlopen", side_effect=RuntimeError("secret-test")):
                with self.assertLogs(level="WARNING") as logs:
                    self.assertFalse(notify("test"))
                self.assertNotIn("secret-test", str(logs.output))

    def test_action_reports_failure_and_preserves_exception(self):
        with patch("app.notifications.notify") as reporter:
            with self.assertRaises(ValueError):
                with action("work"):
                    raise ValueError("test")
            self.assertEqual(reporter.call_args_list[-1].args[0], "work: failed")


if __name__ == "__main__":
    unittest.main()
