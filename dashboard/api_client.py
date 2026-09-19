"""API Client for CodeAuditAgent dashboard."""
import httpx
from typing import Optional

API_BASE = "http://127.0.0.1:9000/api/v1"
TIMEOUT  = 120.0


def _get(path: str, timeout: float = 30.0) -> dict:
    try:
        r = httpx.get(f"{API_BASE}{path}", timeout=timeout)
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.text[:200], "data": {}}
    except Exception as e:
        return {"success": False, "error": str(e), "data": {}}


def _post(path: str, body: dict, timeout: float = TIMEOUT) -> dict:
    try:
        r = httpx.post(f"{API_BASE}{path}", json=body, timeout=timeout)
        if r.status_code in [200, 201, 202]:
            return {"success": True, "data": r.json()}
        return {"success": False, "error": r.json().get("detail", r.text[:200])}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_health() -> dict:
    try:
        r = httpx.get("http://127.0.0.1:9000/health", timeout=5.0)
        if r.status_code == 200:
            return {"success": True, "data": r.json()}
        return {"success": False, "data": {}}
    except Exception:
        return {"success": False, "data": {}}


def list_repositories() -> dict:
    return _get("/repositories/")


def ingest_repository(path: str, name: Optional[str] = None) -> dict:
    return _post("/repositories/", {"path": path, "name": name or path.split("/")[-1]})


def list_scans() -> dict:
    return _get("/scans/")


def start_scan(repository_id: str) -> dict:
    return _post("/scans/", {"repository_id": repository_id})


def get_scan_status(scan_id: str) -> dict:
    return _get(f"/scans/{scan_id}")


def get_findings(scan_id: str) -> dict:
    return _get(f"/findings/{scan_id}")


def get_report(scan_id: str) -> dict:
    return _get(f"/reports/{scan_id}")