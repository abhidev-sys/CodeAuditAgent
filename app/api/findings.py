"""
Findings API endpoints.

Endpoints:
- GET /findings/{scan_id}  — scan ke findings fetch karo
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.finding import FindingResponse, FindingsListResponse
from app.services.scan_service import get_findings, get_scan

router = APIRouter(prefix="/findings", tags=["Findings"])
logger = get_logger("api.findings")


@router.get("/{scan_id}", response_model=FindingsListResponse)
def get_scan_findings(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Scan ke saare findings fetch karo.

    Sirf COMPLETED scans ke findings available hain.
    """
    # Scan exist karta hai check karo
    scan = get_scan(db, str(scan_id))
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Scan is {scan.status} — findings available after completion"
        )

    # Findings fetch karo
    findings = get_findings(db, str(scan_id))

    # Severity counts
    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    high = sum(1 for f in findings if f.severity == "HIGH")
    medium = sum(1 for f in findings if f.severity == "MEDIUM")
    low = sum(1 for f in findings if f.severity == "LOW")

    return FindingsListResponse(
        scan_id=scan_id,
        total=len(findings),
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        findings=[FindingResponse.model_validate(f) for f in findings],
    )