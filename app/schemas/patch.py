"""Patch schemas."""

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class PatchResponse(BaseModel):
    """Single patch response."""
    id: UUID
    finding_id: UUID
    unified_diff: str
    explanation: Optional[str] = None
    confidence: Optional[float] = None
    status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True