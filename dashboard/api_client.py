"""
API Client — Dashboard se API ke saath communicate karta hai.

Yeh layer dashboard views ko API calls se abstract karta hai.
Agar API URL change ho toh sirf yahan change karo.
"""

import httpx
import streamlit as st
from typing import Optional

API_BASE = "http://127.0.0.1:9000/api/v1"
TIMEOUT = 120.0


def ingest_repository(path: str, name: Optional[str] = None) -> dict:
    """Repository ingest karo."""
    try:
        resp = httpx.post(
            f"{API_BASE}/repositories/",
            json={"path": path, "name": name or path.split("/")[-1]},
            timeout=TIMEOUT,
        )
        if resp.status_code == 201:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": resp.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def start_scan(repository_id: str) -> dict:
    """Scan start karo."""
    try:
        resp = httpx.post(
            f"{API_BASE}/scans/",
            json={"repository_id": repository_id},
            timeout=TIMEOUT,
        )
        if resp.status_code in [200, 202]:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": resp.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_scan_status(scan_id: str) -> dict:
    """Scan status fetch karo."""
    try:
        resp = httpx.get(
            f"{API_BASE}/scans/{scan_id}",
            timeout=30.0,
        )
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": "Scan not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_findings(scan_id: str) -> dict:
    """Findings fetch karo."""
    try:
        resp = httpx.get(
            f"{API_BASE}/findings/{scan_id}",
            timeout=30.0,
        )
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": resp.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_report(scan_id: str) -> dict:
    """Report fetch karo."""
    try:
        resp = httpx.get(
            f"{API_BASE}/reports/{scan_id}",
            timeout=30.0,
        )
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": resp.json().get("detail", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_repositories() -> dict:
    """Saari repositories list karo."""
    try:
        resp = httpx.get(f"{API_BASE}/repositories/", timeout=30.0)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": "Failed to fetch repositories"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_scans() -> dict:
    """Saare scans list karo."""
    try:
        resp = httpx.get(f"{API_BASE}/scans/", timeout=30.0)
        if resp.status_code == 200:
            return {"success": True, "data": resp.json()}
        else:
            return {"success": False, "error": "Failed to fetch scans"}
    except Exception as e:
        return {"success": False, "error": str(e)}