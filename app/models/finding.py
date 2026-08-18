from sqlalchemy import Column, String, Integer, Text, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import uuid
from app.core.database import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"))
    vuln_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    confidence = Column(Numeric(5, 2), nullable=True)
    file_path = Column(Text, nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    cwe_id = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    evidence = Column(JSONB, nullable=True)
    exploitability = Column(String(30), nullable=True)
    status = Column(String(30), default="OPEN")
    created_at = Column(DateTime(timezone=True), server_default=func.now())