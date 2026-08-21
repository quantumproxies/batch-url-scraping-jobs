"""Shared HTTP helpers for the batch examples."""
from __future__ import annotations

import os
from typing import Any

import requests

BASE = "https://api.quanticdata.io/v1"
_session = requests.Session()


def _auth() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def post(path: str, body: dict[str, Any], timeout: int = 180) -> dict:
    r = _session.post(f"{BASE}{path}", json=body, headers=_auth(), timeout=timeout)
    data = r.json()
    if data.get("type") == "error" or not r.ok:
        raise RuntimeError(f"POST {path} failed ({r.status_code}): {data.get('message')}")
    return data.get("payload", {})


def get(path: str, timeout: int = 60, **params: Any) -> dict:
    r = _session.get(f"{BASE}{path}", params=params, headers=_auth(), timeout=timeout)
    data = r.json()
    if data.get("type") == "error" or not r.ok:
        raise RuntimeError(f"GET {path} failed ({r.status_code}): {data.get('message')}")
    return data.get("payload", {})
