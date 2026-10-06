"""Send one stored, reviewed draft; does not automatically approve job candidates."""
import argparse
import json
from pathlib import Path
from app.settings import load_env
from app.sources import load_sources
from app.mail_settings import MailSettings
from app.mail_ledger import MailLedger
from app.mailer import send_draft

from app.notifications import action, notify

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", required=True, help="JSON with subject and body")
    parser.add_argument("--job-key", required=True, help="Stable posting key from review")
    parser.add_argument("--recipient", help="Verified recipient JSON")
    parser.add_argument("--resume", required=True, help="Final CV PDF")
    parser.add_argument("--test-to", help="Test destination, must equal SMTP_FROM")
    parser.add_argument("--sources", default="config/sources.json")
    parser.add_argument("--database", default="data/jobs.sqlite3")
    args = parser.parse_args()
    if not args.recipient and not args.test_to:
        parser.error("--recipient or --test-to is required")
    load_env()
    with action("send_draft"):
        draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
        recipient = json.loads(Path(args.recipient).read_text(encoding="utf-8")) if args.recipient else {}
        ledger = MailLedger(args.database)
        try:
            result = send_draft(MailSettings.from_env(), ledger, load_sources(args.sources),
                                args.job_key, recipient, draft, args.resume, args.test_to)
            notify("email: result", result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            ledger.close()
