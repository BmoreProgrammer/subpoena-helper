"""
subpoena_pipeline.clio_client
=============================
Clio API v4 client for subpoena data gathering.
Handles OAuth2, contact search, matter search, and document retrieval.
"""

import requests
import json
import time
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

CLIO_CONFIG = {
    "client_id": "",
    "client_secret": "",
    "redirect_uri": "http://127.0.0.1:11934",
    "base_url": "https://app.clio.com/api/v4",
    "token_file": "config/clio_token.json",
}

@dataclass
class ClioContact:
    id: str
    name: str
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    dob: str
    created_at: str

@dataclass
class ClioMatter:
    id: str
    display_number: str
    case_name: str
    court: str
    case_type: str
    status: str
    open_date: str
    close_date: str
    practice_type: str

@dataclass
class ClioDocument:
    id: str
    filename: str
    matter_id: str
    description: str
    created_at: str

class ClioTokenStore:
    def __init__(self, token_file: str = "config/clio_token.json"):
        self.token_file = Path(token_file)
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Optional[dict]:
        if self.token_file.exists():
            try:
                data = json.loads(self.token_file.read_text())
                if data.get("expires_at", 0) > time.time():
                    return data
            except Exception:
                pass
        return None

    def save(self, token_data: dict):
        token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
        self.token_file.write_text(json.dumps(token_data, indent=2))

    def clear(self):
        if self.token_file.exists():
            self.token_file.unlink()

class ClioClient:
    def __init__(self, client_id: str = None, client_secret: str = None):
        import config as _cfg
        self.client_id = client_id or _cfg.CLIO_CLIENT_ID
        self.client_secret = client_secret or _cfg.CLIO_CLIENT_SECRET
        self.base_url = CLIO_CONFIG["base_url"]
        self.token_store = ClioTokenStore(CLIO_CONFIG["token_file"])
        self.access_token = None
        self._load_token()

    def _load_token(self):
        token_data = self.token_store.load()
        if token_data:
            self.access_token = token_data["access_token"]

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_authorization_url(self) -> str:
        import secrets
        self.state = secrets.token_urlsafe(16)
        return (
            f"https://app.clio.com/oauth/authorize"
            f"?client_id={self.client_id}"
            f"&redirect_uri={CLIO_CONFIG['redirect_uri']}"
            f"&response_type=code"
            f"&state={self.state}"
        )

    def exchange_token(self, code: str) -> dict:
        resp = requests.post(
            "https://app.clio.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": CLIO_CONFIG["redirect_uri"],
            },
            timeout=30,
        )
        resp.raise_for_status()
        token_data = resp.json()
        self.token_store.save(token_data)
        self.access_token = token_data["access_token"]
        return token_data

    def is_connected(self) -> bool:
        if not self.access_token:
            return False
        try:
            self._get("/users")
            return True
        except Exception:
            return False

    def search_contacts(self, query: str, limit: int = 10) -> list[ClioContact]:
        data = self._get("/contacts", params={"filter[query]": query, "limit": limit})
        contacts = []
        for item in data.get("data", []):
            p = item.get("person", {}) or {}
            addr = item.get("primary_address", {}) or {}
            contacts.append(ClioContact(
                id=item["id"],
                name=item.get("name", ""),
                first_name=p.get("first_name", ""),
                last_name=p.get("last_name", ""),
                email=item.get("email", ""),
                phone=item.get("phone", ""),
                address=addr.get("street", "") + ", " + addr.get("city", "") + " " + addr.get("region", "") + " " + (addr.get("postal_code", "") or ""),
                dob=p.get("date_of_birth", ""),
                created_at=item.get("created_at", ""),
            ))
        return contacts

    def search_matters(self, query: str = None, contact_id: str = None, limit: int = 20) -> list[ClioMatter]:
        params = {"limit": limit}
        if query:
            params["filter[query]"] = query
        if contact_id:
            params["filter[contact_id]"] = contact_id
        data = self._get("/matters", params=params)
        matters = []
        for item in data.get("data", []):
            matters.append(ClioMatter(
                id=item["id"],
                display_number=item.get("display_number", ""),
                case_name=item.get("case_name", ""),
                court=item.get("court", ""),
                case_type=item.get("case_type", ""),
                status=item.get("status", ""),
                open_date=item.get("open_date", ""),
                close_date=item.get("close_date", ""),
                practice_type=item.get("practice_type", ""),
            ))
        return matters

    def gather_subpoena_data(self, person_name: str) -> dict:
        contacts = self.search_contacts(person_name)
        matters = self.search_matters(query=person_name)
        all_matters = list(matters)
        for contact in contacts:
            contact_matters = self.search_matters(contact_id=contact.id)
            all_matters.extend(contact_matters)
        seen = set()
        unique_matters = []
        for m in all_matters:
            if m.id not in seen:
                seen.add(m.id)
                unique_matters.append(m)
        return {
            "contacts": [c.__dict__ for c in contacts],
            "matters": [m.__dict__ for m in unique_matters],
            "total_contacts": len(contacts),
            "total_matters": len(unique_matters),
        }