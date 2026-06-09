from datetime import datetime
from pydantic import BaseModel


class ContractCreate(BaseModel):
    """Schema for contract creation. File is uploaded via multipart form."""
    pass


class ContractResponse(BaseModel):
    """Schema for contract list and basic responses."""
    id: str
    filename: str
    file_type: str
    status: str
    overall_risk_score: float | None = None
    risk_level: str | None = None
    risk_breakdown: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClauseInContract(BaseModel):
    """Clause schema used when nested inside ContractDetail."""
    id: str
    clause_type: str
    section_number: str | None = None
    title: str | None = None
    original_text: str
    plain_english_summary: str | None = None
    risk_score: float | None = None
    risk_level: str | None = None
    risk_category: str | None = None
    market_deviation: str | None = None
    deviation_explanation: str | None = None

    model_config = {"from_attributes": True}


class ContractDetail(ContractResponse):
    """Extended contract schema including executive summary and clauses."""
    executive_summary: str | None = None
    clauses: list[ClauseInContract] = []


class ContractList(BaseModel):
    """Wrapper for a list of contracts."""
    contracts: list[ContractResponse]
