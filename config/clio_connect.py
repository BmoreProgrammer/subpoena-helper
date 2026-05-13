#!/usr/bin/env python3
"""Clio OAuth2 connect wizard with cloudflared HTTPS tunnel."""
import http.server
import urllib.parse
import secrets
import time
import sys
import os
import json
import subprocess
import webbrowser
import shutil
import threading
import requests
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

PORT = 11934
CLOUDFLARED_TIMEOUT = 120

def find_cloudflared():
    candidates = [
        Path(__file__).parent.parent / "cloudflared",
        Path("cloudflared"),
        shutil.which("cloudflared"),
    ]
    for p in candidates:
        path = Path(p) if isinstance(p, str) else p
        if path.exists() and path.is_file():
            return str(path.resolve())
    return None

def start_cloudflared_tunnel(port):
    cf_path = find_cloudflared()
    if not cf_path:
        raise FileNotFoundError("cloudflared not found. Download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
    proc = subprocess.Popen([cf_path, "tunnel", "--url", f"http://127.0.0.1:{port}"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    tunnel_url = None
    start = time.time()
    while time.time() - start < CLOUDFLARED_TIMEOUT:
        line = proc.stdout.readline()
        if line and "trycloudflare.com" in line:
            tunnel_url = line.strip()
            while proc.stdout.readline():
                pass
            break
        if proc.poll() is not None:
            raise RuntimeError(f"cloudflared exited: {proc.returncode}")
        time.sleep(0.5)
    if not tunnel_url:
        proc.terminate()
        raise TimeoutError("cloudflared tunnel URL not found")
    return tunnel_url, proc

def stop_cloudflared(proc):
    if proc and proc.poll() is None:
        proc.terminate()

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    code = None
    error = None
    def log_message(self, fmt, *args):
        pass
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "error" in params:
            CallbackHandler.error = params["error"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Error</h1><p>Close this window.</p></body></html>")
            return
        code = params.get("code", [None])[0]
        if code:
            CallbackHandler.code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Success!</h1><p>Close this window.</p></body></html>")

def run_wizard():
    print("=" * 60)
    print("CLIO OAUTH2 CONNECT WIZARD")
    print("=" * 60)
    token_file = Path("config/clio_token.json")
    if token_file.exists():
        try:
            data = json.loads(token_file.read_text())
            if data.get("expires_at", 0) > time.time():
                print("Already connected! Tokens valid.")
                return True
        except:
            pass
    if not config.CLIO_CLIENT_ID or not config.CLIO_CLIENT_SECRET:
        print("ERROR: Set CLIO_CLIENT_ID and CLIO_CLIENT_SECRET in config.py")
        return False
    print(f"Using client_id: {config.CLIO_CLIENT_ID[:8]}...")
    print("\n[1/4] Starting local callback server...")
    server = http.server.HTTPServer(("127.0.0.1", PORT), CallbackHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"  Listening on http://127.0.0.1:{PORT}")
    print("\n[2/4] Starting cloudflared HTTPS tunnel...")
    try:
        tunnel_url, cf_proc = start_cloudflared_tunnel(PORT)
        print(f"  Tunnel URL: {tunnel_url}")
    except Exception as e:
        print(f"ERROR: {e}")
        server.shutdown()
        return False
    print("\n[3/4] Add this URL to your Clio Developer Portal:")
    print(f"\n  >>> {tunnel_url}\n")
    print("  Paste it in the Redirect URI field, save, then press Enter here.")
    input("  Press Enter after saving in the portal...")
    state = secrets.token_urlsafe(16)
    auth_url = f"https://app.clio.com/oauth/authorize?client_id={config.CLIO_CLIENT_ID}&redirect_uri={urllib.parse.quote(tunnel_url)}&response_type=code&state={state}"
    print("\n[4/4] Opening browser to Clio authorization page...")
    webbrowser.open(auth_url)
    print("  Click 'Authorize' in your browser.")
    print("  Waiting for callback...")
    start = time.time()
    while time.time() - start < 180:
        if CallbackHandler.code:
            break
        if CallbackHandler.error:
            break
        time.sleep(1)
    print("Cleaning up...")
    stop_cloudflared(cf_proc)
    server.shutdown()
    thread.join(timeout=5)
    if CallbackHandler.error:
        print(f"ERROR from Clio: {CallbackHandler.error}")
        return False
    if not CallbackHandler.code:
        print("TIMEOUT: No authorization code received.")
        return False
    print("Exchanging for tokens...")
    try:
        resp = requests.post("https://app.clio.com/oauth/token",
            data={"grant_type": "authorization_code", "code": CallbackHandler.code,
                 "client_id": config.CLIO_CLIENT_ID, "client_secret": config.CLIO_CLIENT_SECRET,
                 "redirect_uri": tunnel_url}, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()
        token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
        Path("config/clio_token.json").write_text(json.dumps(token_data, indent=2))
        print(f"SUCCESS! Tokens saved.")
        return True
    except Exception as e:
        print(f"TOKEN EXCHANGE FAILED: {e}")
        return False

if __name__ == "__main__":
    success = run_wizard()
    sys.exit(0 if success else 1)
