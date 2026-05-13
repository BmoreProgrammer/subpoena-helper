# Subpoena Helper

A fully local desktop application for processing legal subpoenas. Court documents never leave your machine.

## Features

- **Auto-detect** subpoena subject name from PDF (no manual entry required)
- **Search local files** for case-related documents (PDFs, TXT, DOCX)
- **LLM-powered field extraction** — pulls case number, court, dates, addresses, etc.
- **Clio integration** — connects to your law firm's Clio account to pull client and matter data
- **100% offline** — after first-run setup, no internet required
- **No server required** — everything runs on your own computer

## Quick Start

1. Download `SubpoenaHelper-Setup.exe` from the Releases page
2. Double-click to install
3. On first run, enter your Clio Developer credentials (see below)
4. Drop a subpoena PDF onto the app and click Process

## Clio Setup (one-time)

1. Go to [app.clio.com/developer](https://app.clio.com/developer) → Create OAuth App
2. When the app shows you a URL, paste it into the **App URL** and **Redirect URI** fields in the Clio portal
3. Copy the **Client ID** and **Client Secret** into Subpoena Helper
4. Click **Clio → Connect to Clio...** in the app menu

## Data Privacy

All document processing happens **100% locally**. The AI model runs entirely offline after the first download. Your court documents are never uploaded to any server.

## System Requirements

- Windows 10/11
- 8GB+ RAM recommended
- ~8GB disk space for AI model