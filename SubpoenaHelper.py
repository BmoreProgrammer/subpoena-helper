#!/usr/bin/env python3
"""SubpoenaHelper - GUI for subpoena pipeline with Clio integration."""
import sys
import os
import subprocess
import shutil
import json
import threading
import tempfile
from pathlib import Path

import PySimpleGUI as sg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

IS_WINDOWS = os.name == "nt"
SCRIPT_DIR = Path(__file__).parent.resolve()
DATA_DIR = SCRIPT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
SUBPOENA_SUBJECT_FILE = DATA_DIR / "current_subject.json"
PIPELINE_OUTPUT_DIR = DATA_DIR / "pipeline_output"
PIPELINE_OUTPUT_DIR.mkdir(exist_ok=True)


def get_version():
    try:
        return open(SCRIPT_DIR / "version.txt").read().strip()
    except:
        return "1.0.0"


class SubpoenaHelperGUI:
    def __init__(self):
        self.clio_connected = is_clio_connected()
        self.current_subject = self._load_current_subject()
        self.window = None

    def _load_current_subject(self):
        if SUBPOENA_SUBJECT_FILE.exists():
            try:
                return json.loads(SUBPOENA_SUBJECT_FILE.read_text())
            except:
                pass
        return None

    def _save_current_subject(self, data):
        SUBPOENA_SUBJECT_FILE.write_text(json.dumps(data, indent=2))
        self.current_subject = data

    def _clear_current_subject(self):
        if SUBPOENA_SUBJECT_FILE.exists():
            SUBPOENA_SUBJECT_FILE.unlink()
        self.current_subject = None

    def build_menu(self):
        clio_status = "Connected ✅" if self.clio_connected else "Not connected"
        return [
            ["File", ["Open PDF...", "Open Folder...", "---", "Exit"]],
            ["Clio", [f"Connect to Clio...", f"Disconnect", f"--- Clio Status: {clio_status}"]],
            ["Help", ["About", "View Logs"]],
        ]

    def build_layout(self):
        subject_card = []
        if self.current_subject:
            s = self.current_subject
            subject_card = [
                [sg.Text(f"📋 Subject: {s.get('name', 'Unknown')}", font=("Default", 11, "bold"))],
                [sg.Text(f"   Case: {s.get('case_number', 'N/A')} | Court: {s.get('court', 'N/A')}", font=("Default", 10))],
                [sg.Text(f"   Confidence: {s.get('confidence', 'N/A')}", font=("Default", 9))],
            ]
        else:
            subject_card = [[sg.Text("No subject loaded. Open a subpoena PDF to begin.", text_color="gray")]]

        left_col = sg.Column([
            [sg.Frame("Subpoena Subject", subject_card, expand_x=True, relief=sg.RELIEF_FLAT, border_width=0)],
            [sg.HorizontalSeparator()],
            [sg.Frame("Processing", [
                [sg.Button("🔍 Extract Fields", size=(18, 1), disabled=True, bind_return_key=True, key="-EXTRACT-")],
                [sg.Button("📂 Search Local Files", size=(18, 1), disabled=True, key="-SEARCH-")],
                [sg.Button("☁️ Search Clio", size=(18, 1), disabled=True, key="-CLIO-")],
                [sg.Button("📊 Generate Report", size=(18, 1), disabled=True, key="-REPORT-")],
            ], expand_x=True)],
            [sg.HorizontalSeparator()],
            [sg.Frame("Status", [[sg.StatusBar("Ready", key="-STATUS-", expand_x=True)]]),
        ], expand_y=True, size=(300, None))

        right_col = sg.Column([
            [sg.Frame("Extracted Fields", [
                [sg.Multiline("", key="-FIELDS-", size=(50, 8), disabled=True, autoscroll=True, write_only=True)]
            ], expand_x=True, expand_y=True)],
            [sg.Frame("Log / Notes", [
                [sg.Multiline("", key="-LOG-", size=(50, 8), disabled=True, autoscroll=True, write_only=True)]
            ], expand_x=True, expand_y=True)],
        ], expand_x=True, expand_y=True)

        return [[sg.Menu(self.build_menu())], [sg.Column([[left_col, right_col]], expand_x=True, expand_y=True)]]

    def create_window(self):
        sg.theme("LightBlue3")
        layout = self.build_layout()
        title = f"Subpoena Helper v{get_version()}"
        self.window = sg.Window(title, layout, resizable=True, finalize=True)
        self._update_clio_menu()

    def _update_clio_menu(self):
        self.window.close()
        self.create_window()

    def run(self):
        self.create_window()
        current_pdf = [None]
        current_pdf_text = [None]

        while True:
            event, values = self.window.read()

            if event in (sg.WINDOW_CLOSED, "Exit"):
                break

            elif event == "Open PDF...":
                path = sg.PopupGetFile("Select Subpoena PDF", file_types=("PDF Files", "*.pdf"),
                                        initial_folder=str(SCRIPT_DIR))
                if path:
                    current_pdf[0] = path
                    self._log("LOG", f"Opened: {Path(path).name}")
                    self.window["-STATUS-"].update("PDF loaded — click 'Extract Fields'")
                    self.window["-EXTRACT-"].update(disabled=False)
                    self.window["-SEARCH-"].update(disabled=False)
                    self.window["-CLIO-"].update(disabled=False)
                    self.window["-REPORT-"].update(disabled=False)

            elif event == "Open Folder...":
                folder = sg.PopupGetFolder("Select Folder of Documents", initial_folder=str(SCRIPT_DIR))
                if folder:
                    self._log("LOG", f"Folder set: {folder}")
                    config.SUBJECT_FILES_FOLDER = folder

            elif event == "-EXTRACT-":
                if not current_pdf[0]:
                    continue
                self._log("LOG", "Extracting fields from PDF...")
                self.window["-STATUS-"].update("Running extraction...")
                threading.Thread(target=self._run_extraction, args=(current_pdf[0],), daemon=True).start()

            elif event == "-SEARCH-":
                if not self.current_subject:
                    continue
                self._log("LOG", "Searching local files...")
                threading.Thread(target=self._run_local_search, daemon=True).start()

            elif event == "-CLIO-":
                if not self.current_subject:
                    continue
                self._log("LOG", "Searching Clio...")
                threading.Thread(target=self._run_clio_search, daemon=True).start()

            elif event == "-REPORT-":
                if not self.current_subject:
                    continue
                self._log("LOG", "Generating report...")
                threading.Thread(target=self._run_report, daemon=True).start()

            elif event == "Connect to Clio...":
                self.run_clio_wizard()

            elif event == "Disconnect":
                self.disconnect_clio()

            elif event == "About":
                sg.popup(f"Subpoena Helper v{get_version()}\n\nAutomate subpoena data gathering with local files + Clio integration.", title="About")

            elif event == "View Logs":
                self.window["-LOG-"].update("")
                self._log("LOG", "Log cleared.")

    def _log(self, prefix, msg):
        timestamp = Path(sg.DEFAULT_TIME_DEBUG_CONFIG).strftime("%H:%M:%S") if hasattr(sg, "DEFAULT_TIME_DEBUG_CONFIG") else ""
        line = f"{prefix}: {msg}\n"
        try:
            self.window["-LOG-"].print(line, end="")
        except:
            print(line, end="")

    def _run_extraction(self, pdf_path):
        from src.pipeline import SubpoenaPipeline
        pipeline = SubpoenaPipeline(
            ollama_url=config.ollama_url(),
            model=config.OLLAMA_MODEL,
            subject_files_folder=getattr(config, "SUBJECT_FILES_FOLDER", None)
        )
        if pipeline.connect_clio():
            self.clio_connected = True
            self._update_clio_menu()
        result = pipeline.run(pdf_path, log_callback=lambda m: self._log("LOG", m))
        if "error" not in result:
            subject_name = result.get("subpoena_subject", "")
            fields = {k: v for k, v in result.items() if not k.startswith("_") and k not in ("pdf_path", "subpoena_subject", "subject_confidence")}
            self.window["-FIELDS-"].update(json.dumps(fields, indent=2))
            self._save_current_subject({
                "name": subject_name,
                "case_number": fields.get("case_number", ""),
                "court": fields.get("court_name", ""),
                "confidence": result.get("subject_confidence", ""),
                "pdf_path": pdf_path,
                "fields": fields,
            })
            self._update_clio_menu()
            self.window["-STATUS-"].update(f"Extracted: {subject_name}")
        else:
            self.window["-STATUS-"].update(f"Error: {result['error']}")

    def _run_local_search(self):
        if not self.current_subject:
            return
        from src.pipeline import SubpoenaPipeline
        pipeline = SubpoenaPipeline(ollama_url=config.ollama_url(), model=config.OLLAMA_MODEL)
        name = self.current_subject["name"]
        result = pipeline.search_local_files(name)
        self._log("FILES", f"Found {result.get('total', 0)} files for '{name}'")
        for f in result.get("files_found", [])[:10]:
            self._log("FILES", f"  {f['file']} ({f['occurrences']} matches) in {f.get('folder','')}")

    def _run_clio_search(self):
        if not self.current_subject or not self.clio_connected:
            return
        from src.pipeline import SubpoenaPipeline
        pipeline = SubpoenaPipeline(ollama_url=config.ollama_url(), model=config.OLLAMA_MODEL)
        pipeline.clio_client = self._get_clio_client()
        pipeline._clio_connected = True
        name = self.current_subject["name"]
        result = pipeline.gather_clio_data(name)
        self._log("CLIO", f"Found {result.get('total_matters', 0)} matters, {result.get('total_contacts', 0)} contacts")
        for c in result.get("contacts", [])[:5]:
            self._log("CLIO", f"  Contact: {c.get('name', 'N/A')} | {c.get('email', '')}")

    def _run_report(self):
        if not self.current_subject:
            return
        sg.popup("Report generation placeholder.\n\nFields and sources will be compiled into a summary.", title="Report")

    def _get_clio_client(self):
        from src.clio_client import ClioClient
        return ClioClient()

    def run_clio_wizard(self):
        if not config.CLIO_CLIENT_ID or not config.CLIO_CLIENT_SECRET:
            sg.popup("Configure CLIO_CLIENT_ID and CLIO_CLIENT_SECRET in config.py first.", title="Clio Not Configured")
            return
        script = SCRIPT_DIR / "config" / "clio_connect.py"
        if not script.exists():
            sg.popup(f"clio_connect.py not found at:\n{script}", title="Error")
            return
        try:
            if IS_WINDOWS:
                subprocess.Popen(["python", str(script)], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["python3", str(script)], start_new_session=True)
            sg.popup("Clio wizard is running in a new terminal window.\n\nFollow the steps in that terminal.", title="Clio Connect")
        except Exception as e:
            sg.popup(f"Failed to start wizard:\n{e}", title="Error")

    def disconnect_clio(self):
        token_file = SCRIPT_DIR / "config" / "clio_token.json"
        if token_file.exists():
            token_file.unlink()
        self.clio_connected = False
        self._update_clio_menu()
        self.window["-STATUS-"].update("Clio disconnected.")


def is_clio_connected():
    token_file = SCRIPT_DIR / "config" / "clio_token.json"
    if not token_file.exists():
        return False
    try:
        data = json.loads(token_file.read_text())
        return data.get("expires_at", 0) > time.time()
    except:
        return False


if __name__ == "__main__":
    import time
    SubpoenaHelperGUI().run()
