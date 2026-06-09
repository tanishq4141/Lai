import uuid

from sqlalchemy import Column, String, Text, JSON

from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    contract_type = Column(String(50), nullable=False)
    # Contract types: nda, saas, employment, services
    clause_type = Column(String(50), nullable=False)
    standard_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    acceptable_variations = Column(JSON, nullable=True)

    def __repr__(self) -> str:
        return f"<Baseline {self.contract_type}/{self.clause_type}>"
