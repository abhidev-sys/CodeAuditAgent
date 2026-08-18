from sqlalchemy import Column, String, Text, ForeignKey, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Patch(Base):
    __tablename__ = "patches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"))
    unified_diff = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    confidence = Column(Numeric(5, 2), nullable=True)
    status = Column(String(30), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())