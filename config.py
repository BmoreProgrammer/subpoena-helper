SubpoenaHelper — Configuration
==============================
Edit these settings to configure how SubpoenaHelper connects to Ollama.

# ---------------------------------------------------------------------------
# OLLAMA CONNECTION
# ---------------------------------------------------------------------------

# True = connect to a remote Ollama server (your server)
# False = use local Ollama bundled in this folder
USE_REMOTE = False

# URL of your Ollama server (used if USE_REMOTE = True)
# Example: "http://192.168.1.100:11434" or "https://your-server.com:11434"
OLLAMA_URL = "http://localhost:11434"

def ollama_url() -> str:
    """Return the Ollama URL based on USE_REMOTE setting."""
    return OLLAMA_URL if USE_REMOTE else "http://localhost:11434"

# AI model to use
MODEL_NAME = "gemma4:e2b"

# Fallback model if primary isn't available
FALLBACK_MODEL = "gemma4:e2b"

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

# Path to local Ollama binary (relative to this folder)
OLLAMA_EXE = "ollama.exe"

# Path to subject_files folder (documents to search)
SUBJECT_FILES_FOLDER = "data/subject_files"

# ---------------------------------------------------------------------
# CLIO OAUTH (optional — needed to search Clio for client/matter data)
# ---------------------------------------------------------------------
# Get these from https://app.clio.com/developer → Create OAuth App
# Redirect URI in portal must be: http://127.0.0.1:11934
CLIO_CLIENT_ID = ""
CLIO_CLIENT_SECRET = ""
CLIO_REDIRECT_URI = "http://127.0.0.1:11934"

# ---------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------

GUI_THEME = "SystemDefault"  # "SystemDefault" = follows Windows/Mac theme