"""Finding schemas."""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class FindingResponse(BaseModel):
    """Single finding response."""
    id: UUID
    scan_id: UUID
    vuln_type: str
    severity: str
    confidence: Optional[float] = None
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    cwe_id: Optional[str] = None
    description: Optional[str] = None
    evidence: Optional[dict] = None
    exploitability: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FindingsListResponse(BaseModel):
    """Multiple findings response."""
    scan_id: UUID
    total: int
    critical: int
    high: int
    medium: int
    low: int
    findings: list[FindingResponse]