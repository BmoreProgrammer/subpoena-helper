# -*- coding: utf-8 -*-
"""
Subpoena Helper - Configuration
All settings for the subpoena pipeline.
"""

import socket
import os
from pathlib import Path

# ─── Ollama ────────────────────────────────────────────────────────────────

def _detect_ollama():
    """Detect if Ollama is running on the local machine or a known server."""
    host = os.environ.get("OLLAMA_HOST", "")
    if host:
        return host
    # Try localhost first
    try:
        import requests
        r = requests.get("http://localhost:11434", timeout=2)
        if r.status_code == 200:
            return "http://localhost:11434"
    except:
        pass
    # Try the known server
    try:
        import requests
        r = requests.get("http://192.168.1.165:11434", timeout=2)
        if r.status_code == 200:
            return "http://192.168.1.165:11434"
    except:
        pass
    return "http://localhost:11434"

OLLAMA_HOST = _detect_ollama()
OLLAMA_MODEL = "gemma4:e2b"

def ollama_url():
    return OLLAMA_HOST

# ─── Clio OAuth ───────────────────────────────────────────────────────────

CLIO_CLIENT_ID = ""
CLIO_CLIENT_SECRET = ""
CLIO_REDIRECT_URI = "http://127.0.0.1:11934"

# ─── File Paths ───────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
SUBJECT_FILES_FOLDER = None  # Set by user via GUI

# ─── Logging ───────────────────────────────────────────────────────────────

LOG_FILE = DATA_DIR / "pipeline.log"
