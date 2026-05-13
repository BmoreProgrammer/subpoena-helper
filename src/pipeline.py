"""Subpoena Pipeline - Multi-source data gathering with LLM matching."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import time
from pathlib import Path
from typing import Optional

from src.pdf_extractor import extract_subpoena_text
from src.clio_client import ClioClient

SUBJECT_EXTRACTION_PROMPT = """You are a legal document analyst. Given the text of a subpoena document, identify the FULL LEGAL NAME of the person this subpoena is about (the subpoena subject / respondent / person whose information is being sought).

Look for patterns like:
- "IN THE MATTER OF [NAME]"
- "SUBPOENA TO: [NAME]"
- "RE: [NAME]"
- "Subpoena for: [NAME]"

Return a JSON object with:
- "subject_name": the full legal name
- "subject_role": the role (respondent, witness, deponent)
- "confidence": high, medium, or low
- "reasoning": brief explanation

Respond ONLY with valid JSON."""

FIELD_EXTRACTION_PROMPT = """You are a legal document analyst. Given a subpoena PDF, extract ALL of the following fields:

1. case_number
2. court_name
3. subpoena_type
4. issue_date
5. respondent_name
6. respondent_address
7. respondent_phone
8. respondent_email
9. attorney_name
10. attorney_bar_number
11. hearing_date
12. hearing_time
13. hearing_location
14. documents_requested
15. penalty_clause
16. notes

Return a JSON object with all found fields (null if not found). Add a confidence field."""

class SubpoenaPipeline:
    def __init__(self, ollama_url: str = "http://localhost:11434",
                 model: str = "gemma4:e2b",
                 subpoena_subject: str = None,
                 subject_files_folder: str = None):
        self.ollama_url = ollama_url
        self.model = model
        self.subpoena_subject = subpoena_subject
        self.subject_files_folder = subject_files_folder
        self.clio_client = None
        self._clio_connected = False

    def llm_chat(self, prompt: str) -> str:
        import requests
        resp = requests.post(
            f"{self.ollama_url}/api/chat",
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")

    def llm_generate(self, prompt: str) -> str:
        import requests
        resp = requests.post(
            f"{self.ollama_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    def extract_subpoena_subject(self, pdf_text: str) -> tuple[str, str]:
        prompt = SUBJECT_EXTRACTION_PROMPT + f"\n\nDOCUMENT TEXT:\n{pdf_text[:4000]}"
        response = self.llm_chat(prompt)
        try:
            result = json.loads(response)
            name = result.get("subject_name", "") or ""
            confidence = result.get("confidence", "low")
            reasoning = result.get("reasoning", "")
            return name, f"{confidence} confidence — {reasoning}"
        except:
            patterns = [
                r'IN THE MATTER OF[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
                r'SUBPOENA TO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
                r'RE:[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            ]
            for pat in patterns:
                m = re.search(pat, pdf_text)
                if m:
                    return m.group(1), "medium confidence — pattern match"
        return "", "could not determine"

    def extract_fields(self, pdf_text: str) -> dict:
        prompt = FIELD_EXTRACTION_PROMPT + f"\n\nDOCUMENT TEXT:\n{pdf_text[:6000]}"
        response = self.llm_chat(prompt)
        try:
            result = json.loads(response)
            return result
        except:
            return {"error": "Could not parse response", "raw": response[:500]}

    def connect_clio(self) -> bool:
        try:
            self.clio_client = ClioClient()
            self._clio_connected = self.clio_client.is_connected()
            return self._clio_connected
        except:
            self._clio_connected = False
            return False

    def search_local_files(self, subject_name: str) -> dict:
        import fitz
        root = Path(self.subject_files_folder) if self.subject_files_folder else None
        if not root or not root.exists():
            return {"files_found": [], "total": 0}
        name_parts = subject_name.split()
        results = []
        for ext in ["*.pdf", "*.txt", "*.docx"]:
            for file_path in root.rglob(ext):
                try:
                    if file_path.suffix == ".pdf":
                        doc = fitz.open(str(file_path))
                        text = "".join(page.get_text() for page in doc)
                        doc.close()
                    elif file_path.suffix == ".txt":
                        text = file_path.read_text(errors="ignore")
                    elif file_path.suffix == ".docx":
                        from docx import Document
                        doc = Document(str(file_path))
                        text = "\n".join(p.text for p in doc.paragraphs)
                    else:
                        continue
                    if not text:
                        continue
                    count = sum(text.lower().count(p.lower()) for p in name_parts)
                    if count > 0:
                        results.append({"file": str(file_path.name), "folder": file_path.parent.name, "occurrences": count})
                except:
                    continue
        results.sort(key=lambda x: x["occurrences"], reverse=True)
        return {"files_found": results, "total": len(results), "search_root": str(root), "subject_name": subject_name}

    def gather_clio_data(self, person_name: str) -> dict:
        if not self._clio_connected:
            return {"contacts": [], "matters": [], "total_contacts": 0, "total_matters": 0}
        return self.clio_client.gather_subpoena_data(person_name)

    def combine_and_fill(self, fields: dict, file_data: dict, clio_data: dict) -> dict:
        combined = dict(fields)
        combined["_sources"] = {
            "pdf_extraction": True,
            "local_files": file_data.get("total", 0) > 0,
            "clio": clio_data.get("total_matters", 0) > 0,
        }
        combined["_file_matches"] = file_data.get("files_found", [])
        combined["_clio_contacts"] = clio_data.get("contacts", [])
        combined["_clio_matters"] = clio_data.get("matters", [])
        return combined

    def run(self, pdf_path: str, log_callback=None) -> dict:
        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

        log(f"Processing: {pdf_path}")
        pdf_text = extract_subpoena_text(pdf_path)
        if not pdf_text:
            return {"error": "Could not extract text from PDF"}

        subject, note = self.extract_subpoena_subject(pdf_text)
        log(f"Subject: {subject} ({note})")

        fields = self.extract_fields(pdf_text)
        log(f"Extracted {len([k for k in fields if fields[k]])} fields")

        file_data = self.search_local_files(subject) if subject else {"files_found": [], "total": 0}
        log(f"Found {file_data.get('total', 0)} local files")

        clio_data = self.gather_clio_data(subject) if subject else {}
        log(f"Found {clio_data.get('total_matters', 0)} Clio matters")

        result = self.combine_and_fill(fields, file_data, clio_data)
        result["subpoena_subject"] = subject
        result["subject_confidence"] = note
        result["pdf_path"] = pdf_path
        return result