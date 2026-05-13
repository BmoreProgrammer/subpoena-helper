"""
subpoena_pipeline.pdf_extractor
================================
PDF text extraction using PyMuPDF.
"""

import fitz  # PyMuPDF
from pathlib import Path

def extract_subpoena_text(pdf_path: str) -> str | None:
    """Extract all text from a PDF file. Returns None if encrypted or unreadable."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text if text.strip() else None
    except Exception as e:
        return None

def extract_subpoena_fields(text: str) -> dict:
    """Simple field extraction from subpoena text using patterns."""
    import re
    fields = {}

    patterns = {
        "case_number": r"Case No[.:]?\s*([A-Z0-9\-]+)",
        "court_name": r"IN THE\s+([A-Z][\w\s]+COURT)",
        "issue_date": r"Issued(?: on)?\s*([A-Z][a-z]+ \d{1,2},? \d{4})",
        "respondent_name": r"SUBPOENA TO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)",
        "respondent_address": r"\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s+\d{5}",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            fields[field] = match.group(1).strip()

    return fields