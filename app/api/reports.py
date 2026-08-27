"""
Reports API endpoints.

Endpoints:
- GET /reports/{scan_id}  — scan ka report fetch karo
"""

import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.logger import get_logger
from app.schemas.report import ReportResponse, FullReportResponse
from app.services.scan_service import get_report, get_scan

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = get_logger("api.reports")


@router.get("/{scan_id}", response_model=FullReportResponse)
def get_scan_report(
    scan_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Scan ka complete report fetch karo.

    Sirf COMPLETED scans ka report available hai.
    """
    scan = get_scan(db, str(scan_id))
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"Scan is {scan.status} — report available after completion"
        )

    report = get_report(db, str(scan_id))
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # JSON report file padho
    if report.report_path and Path(report.report_path).exists():
        with open(report.report_path, encoding="utf-8") as f:
            report_data = json.load(f)

        return FullReportResponse(
            report_id=report_data.get("report_id", ""),
            scan_id=str(scan_id),
            repository_name=report_data.get("repository", {}).get("name", ""),
            risk_score=report_data.get("risk_assessment", {}).get("score", 0),
            risk_level=report_data.get("risk_assessment", {}).get("level", ""),
            executive_summary=report_data.get("executive_summary", ""),
            findings_summary=report_data.get("findings_summary", {}),
            patch_summary=report_data.get("patch_summary", {}),
            findings=report_data.get("findings", []),
            recommendations=report_data.get("recommendations", []),
            generated_at=report_data.get("generated_at", ""),
        )

    raise HTTPException(status_code=404, detail="Report file not found")