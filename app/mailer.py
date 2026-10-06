"""Send a verified draft with a PDF resume, quota and duplicate guards."""
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path
from .mail_settings import valid_email
from .sources import is_allowed_url


def verify_recipient(recipient, sources):
    if not isinstance(recipient, dict) or not valid_email(recipient.get("email")):
        raise ValueError("Invalid recipient email.")
    if recipient.get("verified") is not True or recipient.get("purpose") != "job_application":
        raise ValueError("Recipient must be verified for job applications.")
    if not is_allowed_url(recipient.get("source_url", ""), sources):
        raise ValueError("Recipient source must be on an approved domain.")
    evidence = recipient.get("source_evidence", "")
    if not isinstance(evidence, str) or recipient["email"].lower() not in evidence.lower():
        raise ValueError("Source evidence must contain the exact recruiting email.")
    # These fields are an attestation; this module does not browse/verify source text.
    return recipient["email"]


def build_message(settings, to_email, draft, resume):
    if not valid_email(to_email):
        raise ValueError("Invalid email destination.")
    subject = draft.get("subject", "")
    body = draft.get("body", "")
    if (not isinstance(subject, str) or not subject.strip() or len(subject) > 200
            or "\n" in subject or "\r" in subject
            or not isinstance(body, str) or not body.strip()):
        raise ValueError("Invalid email draft.")
    data = Path(resume).read_bytes()
    if not data.startswith(b"%PDF-") or len(data) > 10 * 1024 * 1024:
        raise ValueError("Resume must be a PDF no larger than 10 MiB.")
    message = EmailMessage()
    message["From"] = settings.sender
    message["To"] = to_email
    message["Subject"] = subject
    message["Message-ID"] = make_msgid()
    message.set_content(body)
    message.add_attachment(data, maintype="application", subtype="pdf", filename="resume.pdf")
    return message


def smtp_send(settings, message):
    context = ssl.create_default_context()
    if settings.tls_mode == "ssl":
        client = smtplib.SMTP_SSL(settings.host, settings.port, timeout=30, context=context)
    else:
        client = smtplib.SMTP(settings.host, settings.port, timeout=30)
    with client:
        if settings.tls_mode == "starttls":
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        client.login(settings.username, settings.password)
        refused = client.send_message(message)
        if refused:
            raise RuntimeError("SMTP refused recipient.")


def send_draft(settings, ledger, sources, job_key, recipient, draft, resume,
               test_to=None, transport=smtp_send):
    if not isinstance(job_key, str) or not job_key.strip():
        raise ValueError("Stable job key is required.")
    if test_to is not None:
        if test_to != settings.sender:
            raise ValueError("Test destination must equal SMTP_FROM.")
        to_email = test_to
        reservation_key = "test:" + job_key
    else:
        to_email = verify_recipient(recipient, sources)
        reservation_key = job_key
    message = build_message(settings, to_email, draft, resume)
    if not settings.enabled:
        return {"status": "dry_run", "to": to_email, "subject": message["Subject"]}
    ledger.reserve(reservation_key, to_email, message["Message-ID"], settings.daily_limit)
    try:
        transport(settings, message)
    except Exception:
        ledger.finish(reservation_key, "uncertain")
        raise
    ledger.finish(reservation_key, "sent")
    return {"status": "sent", "to": to_email, "message_id": message["Message-ID"]}
