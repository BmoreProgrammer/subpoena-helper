# Subpoena Helper

A fully local desktop application for processing legal subpoenas. Court documents never leave your machine.

## Features

- **Auto-detect** subpoena subject name from PDF (no manual entry required)
- **Search local files** for case-related documents (PDFs, TXT, DOCX)
- **LLM-powered field extraction** — pulls case number, court, dates, addresses, etc.
- **Clio integration** — connects to your law firm's Clio account to pull client and matter data
- **100% offline** — after first-run setup, no internet required
- **No server required** — everything runs on your own computer

## Requirements

- Windows 10/11
- Python 3.10+ (installed automatically by setup)

## Quick Start

1. Download `SubpoenaHelper-Setup.exe` from the Releases page
2. Double-click to install
3. On first run, enter your Clio Developer credentials:
   - Go to [app.clio.com/developer](https://app.clio.com/developer)
   - Create an OAuth App
   - Add the redirect URI shown by the app
   - Copy Client ID and Client Secret into the app
4. Drop a subpoena PDF onto the app and click Process

## How It Works

```
Subpoena PDF → Local LLM → Auto-detect subject name
                    ↓
         Local file search (subject_files folder)
                    ↓
         Clio API (contacts + matters)
                    ↓
         Structured JSON output with all fields
```

## Data Privacy

All document processing happens **100% locally** on your machine. The AI model runs entirely offline after the first download. Your court documents are never uploaded to any server.

## Clio Setup

1. Go to [app.clio.com/developer](https://app.clio.com/developer)
2. Click "Create OAuth App"
3. Use the URL provided by the app as both App URL and Redirect URI
4. Copy the Client ID and Client Secret into Subpoena Helper
5. Click "Clio → Connect to Clio..." in the app menu

## Support

For issues or questions, contact your IT administrator.