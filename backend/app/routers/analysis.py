from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.contract import Contract
from app.models.clause import Clause
from app.schemas.analysis import (
    AnalysisStatus,
    ClauseResponse,
    ExecutiveSummary,
    RiskBreakdown,
)
from app.services.pipeline import run_analysis_pipeline

router = APIRouter(prefix="/api/contracts", tags=["analysis"])


@router.post("/{contract_id}/analyze", response_model=AnalysisStatus)
async def trigger_analysis(
    contract_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger the AI analysis pipeline for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if contract.status in ("analyzing", "parsing"):
        raise HTTPException(
            status_code=409,
            detail="Analysis is already in progress for this contract",
        )

    # Update status
    contract.status = "parsing"
    db.commit()

    # Launch background analysis
    background_tasks.add_task(
        run_analysis_pipeline,
        contract_id=contract_id,
        db_url=settings.DATABASE_URL,
    )

    return AnalysisStatus(
        contract_id=contract_id,
        status="parsing",
        progress=0.0,
        message="Analysis pipeline started",
    )


@router.get("/{contract_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(
    contract_id: str,
    db: Session = Depends(get_db),
):
    """Get the current analysis status for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Map status to progress percentage
    progress_map = {
        "uploaded": 0.0,
        "parsing": 0.2,
        "parsed": 0.4,
        "analyzing": 0.6,
        "complete": 1.0,
        "error": 0.0,
    }

    return AnalysisStatus(
        contract_id=contract_id,
        status=contract.status,
        progress=progress_map.get(contract.status, 0.0),
        message=f"Contract is currently: {contract.status}",
    )


@router.get("/{contract_id}/clauses", response_model=list[ClauseResponse])
async def get_contract_clauses(
    contract_id: str,
    db: Session = Depends(get_db),
):
    """Get all extracted clauses for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    clauses = (
        db.query(Clause)
        .filter(Clause.contract_id == contract_id)
        .order_by(Clause.position)
        .all()
    )
    return clauses


@router.get("/{contract_id}/summary", response_model=ExecutiveSummary)
async def get_executive_summary(
    contract_id: str,
    db: Session = Depends(get_db),
):
    """Get the AI-generated executive summary for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.executive_summary:
        raise HTTPException(
            status_code=404,
            detail="Executive summary not yet available. Run analysis first.",
        )

    # Parse the stored summary (expects JSON-compatible structure)
    return ExecutiveSummary(
        summary=contract.executive_summary,
        key_terms=[],
        risk_carrier="",
        top_issues=[],
    )


@router.get("/{contract_id}/risks", response_model=RiskBreakdown)
async def get_risk_breakdown(
    contract_id: str,
    db: Session = Depends(get_db),
):
    """Get the risk breakdown scores for a contract."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if not contract.risk_breakdown:
        raise HTTPException(
            status_code=404,
            detail="Risk breakdown not yet available. Run analysis first.",
        )

    return RiskBreakdown(**contract.risk_breakdown)
