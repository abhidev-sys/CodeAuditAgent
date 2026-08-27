"""
Scan API ke liye Pydantic schemas.

ORM Model = database table
Pydantic Schema = API input/output validation
"""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class ScanCreate(BaseModel):
    """POST /scans ke liye request body."""
    repository_id: UUID = Field(..., description="Repository UUID jo scan karni hai")
    model_override: Optional[str] = Field(
        None,
        description="Optional model override e.g. openai/gpt-oss-120b"
    )


class ScanResponse(BaseModel):
    """Scan ka basic response."""
    id: UUID
    repository_id: UUID
    status: str
    risk_score: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScanStatusResponse(BaseModel):
    """Scan status response with details."""
    id: UUID
    status: str
    risk_score: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    message: str

    class Config:
        from_attributes = True