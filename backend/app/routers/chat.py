from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract import Contract
from app.models.clause import Clause
from app.schemas.analysis import ChatRequest, ChatResponse
from app.services.chat import chat_with_contract as chat_service

router = APIRouter(prefix="/api/contracts", tags=["chat"])


@router.post("/{contract_id}/chat", response_model=ChatResponse)
async def chat_with_contract(
    contract_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """Chat with an AI assistant about a specific contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.raw_text:
        raise HTTPException(
            status_code=400,
            detail="Contract has not been parsed yet. Run analysis first.",
        )

    # Get extracted clauses for context
    clauses = (
        db.query(Clause)
        .filter(Clause.contract_id == contract_id)
        .order_by(Clause.position)
        .all()
    )

    clause_dicts = [
        {
            "clause_type": c.clause_type,
            "section_number": c.section_number,
            "title": c.title,
        }
        for c in clauses
    ]

    try:
        result = await chat_service(
            question=request.message,
            contract_text=contract.raw_text,
            clauses=clause_dicts,
        )
        return ChatResponse(
            response=result.get("response", "I could not generate a response."),
            citations=result.get("citations", []),
        )
    except Exception as e:
        return ChatResponse(
            response=f"I encountered an error while analyzing the contract: {str(e)}",
            citations=[],
        )

