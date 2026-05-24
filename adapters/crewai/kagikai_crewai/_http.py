"""Synchronous HTTP helper for Kagikai ICS API calls."""

import os

import httpx


class KagikaiAPI:
    """Thin sync HTTP client for the Kagikai ICS REST API."""

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self.base_url: str = (base_url or os.environ.get("KAGIKAI_BASE_URL", "")).rstrip("/")
        self.api_key: str = api_key or os.environ.get("KAGIKAI_API_KEY", "")

    def _headers(self, auth: bool = True) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if auth and self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def get(self, path: str, auth: bool = True) -> dict:
        with httpx.Client(timeout=30.0) as c:
            r = c.get(f"{self.base_url}{path}", headers=self._headers(auth))
            r.raise_for_status()
            return r.json()

    def post(self, path: str, body: dict, auth: bool = True) -> dict:
        with httpx.Client(timeout=30.0) as c:
            r = c.post(f"{self.base_url}{path}", json=body, headers=self._headers(auth))
            r.raise_for_status()
            return r.json()

    def put(self, path: str, body: dict, auth: bool = True) -> dict:
        with httpx.Client(timeout=30.0) as c:
            r = c.put(f"{self.base_url}{path}", json=body, headers=self._headers(auth))
            r.raise_for_status()
            return r.json()

    def delete(self, path: str, auth: bool = True) -> dict:
        with httpx.Client(timeout=30.0) as c:
            r = c.delete(f"{self.base_url}{path}", headers=self._headers(auth))
            r.raise_for_status()
            return r.json()
