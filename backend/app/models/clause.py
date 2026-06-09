import uuid

from sqlalchemy import Column, String, Text, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_id = Column(String(36), ForeignKey("contracts.id"), nullable=False)
    clause_type = Column(String(50), nullable=False)
    # Clause types: indemnity, liability, governing_law, termination,
    # ip_ownership, payment, confidentiality, other
    section_number = Column(String(20), nullable=True)
    title = Column(String(255), nullable=True)
    original_text = Column(Text, nullable=False)
    plain_english_summary = Column(Text, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    risk_category = Column(String(20), nullable=True)
    # Risk categories: financial, operational, legal, reputational
    market_deviation = Column(String(20), nullable=True)
    # Deviation values: favourable, unfavourable, unusual, standard
    deviation_explanation = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    position = Column(Integer, nullable=True)

    contract = relationship("Contract", back_populates="clauses")

    def __repr__(self) -> str:
        return f"<Clause {self.clause_type} (contract={self.contract_id})>"
