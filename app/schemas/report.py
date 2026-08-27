"""Report schemas."""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class ReportResponse(BaseModel):
    """Report response."""
    id: UUID
    scan_id: UUID
    summary: Optional[dict] = None
    report_path: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class FullReportResponse(BaseModel):
    """Complete report with all details."""
    report_id: str
    scan_id: str
    repository_name: str
    risk_score: int
    risk_level: str
    executive_summary: str
    findings_summary: dict
    patch_summary: dict
    findings: list[dict]
    recommendations: list[str]
    generated_at: str