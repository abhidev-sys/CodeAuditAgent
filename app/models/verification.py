from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patch_id = Column(UUID(as_uuid=True), ForeignKey("patches.id"))
    regression_pass = Column(Boolean, nullable=True)
    security_rescan = Column(Boolean, nullable=True)
    static_rescan = Column(Boolean, nullable=True)
    overall_result = Column(String(30), nullable=True)
    test_output = Column(JSONB, nullable=True)
    rescan_output = Column(JSONB, nullable=True)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())