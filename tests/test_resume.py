"""Real PDF extraction and missing/unreadable resume checks; no network."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from app.resume import load_candidate_profile, load_resume_profile, resume_path


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "resume.pdf"

    def tearDown(self):
        self.tmp.cleanup()

    def write_pdf(self, text=True, password=None):
        writer = PdfWriter()
        page = writer.add_blank_page(width=600, height=800)
        if text:
            font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                     NameObject("/Subtype"): NameObject("/Type1"),
                                     NameObject("/BaseFont"): NameObject("/Helvetica"),
                                     NameObject("/Encoding"): NameObject("/WinAnsiEncoding")})
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
            stream = DecodedStreamObject()
            stream.set_data(b"BT /F1 12 Tf 10 10 Td (DevOps Kubernetes Engineer) Tj ET")
            page[NameObject("/Contents")] = writer._add_object(stream)
        if password:
            writer.encrypt(password)
        writer.write(self.path)

    def test_extract_pdf_from_configured_path(self):
        self.write_pdf()
        with patch.dict(os.environ, {"RESUME_PATH": str(self.path)}):
            self.assertIn("Kubernetes", load_candidate_profile()["resume_text"])

    def test_cli_path_overrides_env(self):
        with patch.dict(os.environ, {"RESUME_PATH": "other.pdf"}):
            self.assertEqual(resume_path(self.path), self.path)

    def test_missing_and_invalid_pdf_fail(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            load_resume_profile(self.path)
        self.path.write_bytes(b"not a pdf")
        with self.assertRaisesRegex(ValueError, "PDF file"):
            load_resume_profile(self.path)
        self.path.write_bytes(b"%PDF-1.4\ninvalid")
        with self.assertRaises(ValueError):
            load_resume_profile(self.path)

    def test_blank_and_encrypted_pdf_fail(self):
        self.write_pdf(text=False)
        with self.assertRaisesRegex(ValueError, "no extractable text"):
            load_resume_profile(self.path)
        self.write_pdf(password="test")
        with self.assertRaisesRegex(ValueError, "unencrypted"):
            load_resume_profile(self.path)

    def test_existing_json_profile_supported(self):
        profile = self.path.with_suffix(".json")
        profile.write_text(json.dumps({"name": "Test"}))
        self.assertEqual(load_candidate_profile(profile), {"name": "Test"})
        with self.assertRaises(ValueError):
            load_candidate_profile(profile, self.path)


if __name__ == "__main__":
    unittest.main()
