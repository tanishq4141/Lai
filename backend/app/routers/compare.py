from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.clause import Clause
from app.models.contract import Contract
from app.schemas.analysis import CompareRequest, CompareResult, ClauseComparison

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.post("", response_model=CompareResult)
async def compare_clauses(
    request: CompareRequest,
    db: Session = Depends(get_db),
):
    """Compare clauses of a specific type across multiple contracts."""
    # Validate that all contracts exist
    for cid in request.contract_ids:
        contract = db.query(Contract).filter(Contract.id == cid).first()
        if not contract:
            raise HTTPException(
                status_code=404,
                detail=f"Contract {cid} not found",
            )

    # Fetch clauses of the specified type from all given contracts
    clauses = (
        db.query(Clause)
        .filter(
            Clause.contract_id.in_(request.contract_ids),
            Clause.clause_type == request.clause_type,
        )
        .all()
    )

    comparisons = [
        ClauseComparison(
            contract_id=clause.contract_id,
            clause_text=clause.original_text,
            risk_score=clause.risk_score,
            deviation=clause.market_deviation,
        )
        for clause in clauses
    ]

    return CompareResult(
        clause_type=request.clause_type,
        comparisons=comparisons,
    )
