"""Load the local PDF resume for drafting; never download or log its contents."""
import json
import os
from pathlib import Path
from pypdf import PdfReader


def resume_path(value=None):
    return Path(value or os.getenv("RESUME_PATH", "resume.pdf"))


def load_resume_profile(value=None):
    path = resume_path(value)
    if not path.is_file():
        raise ValueError("Resume PDF is missing. Place resume.pdf beside Dockerfile or set RESUME_PATH.")
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Resume PDF must be no larger than 10 MiB.")
    with path.open("rb") as source:
        if source.read(5) != b"%PDF-":
            raise ValueError("Resume must be a PDF file.")
        source.seek(0)
        try:
            reader = PdfReader(source)
            if reader.is_encrypted:
                raise ValueError("Resume must be an unencrypted PDF.")
            if len(reader.pages) > 30:
                raise ValueError("Resume PDF must contain at most 30 pages.")
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except ValueError:
            raise
        except Exception as error:
            raise ValueError("Cannot read resume PDF; export a valid text PDF.") from error
    if not text:
        raise ValueError("Resume PDF has no extractable text. Export a text PDF; OCR is not included.")
    if len(text) > 100_000:
        raise ValueError("Resume text is too large (maximum 100000 characters).")
    return {"resume_text": text}


def load_candidate_profile(profile=None, resume=None):
    if profile and resume:
        raise ValueError("Choose either --profile or --resume.")
    if profile:
        result = json.loads(Path(profile).read_text(encoding="utf-8"))
        if not isinstance(result, dict) or not result:
            raise ValueError("Profile must be a nonempty object with verified CV facts.")
        return result
    return load_resume_profile(resume)
