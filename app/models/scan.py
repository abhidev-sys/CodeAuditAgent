from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    status = Column(String(50), nullable=False, default="PENDING")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    risk_score = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    token_usage = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    agent_trace = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())