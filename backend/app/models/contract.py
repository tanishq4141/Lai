import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx
    status = Column(String(20), default="uploaded")
    # Status values: uploaded, parsing, parsed, analyzing, complete, error
    raw_text = Column(Text, nullable=True)
    parsed_structure = Column(JSON, nullable=True)
    overall_risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high, critical
    risk_breakdown = Column(JSON, nullable=True)
    # Risk breakdown keys: financial, operational, legal, reputational
    executive_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    clauses = relationship("Clause", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Contract {self.filename} ({self.status})>"
