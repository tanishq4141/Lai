import os
import uuid
import shutil

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.contract import Contract
from app.schemas.contract import ContractResponse, ContractDetail, ContractList

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.post("/upload", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a contract document (PDF or DOCX) for analysis."""
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if extension not in ("pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX files are accepted.",
        )

    # Validate file size
    contents = await file.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum of {settings.MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Save file to disk
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Create database record
    contract = Contract(
        id=file_id,
        filename=file.filename,
        file_path=file_path,
        file_type=extension,
        status="uploaded",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    return contract


@router.get("", response_model=ContractList)
async def list_contracts(db: Session = Depends(get_db)):
    """List all uploaded contracts."""
    contracts = db.query(Contract).order_by(Contract.created_at.desc()).all()
    return ContractList(contracts=contracts)


@router.get("/{contract_id}", response_model=ContractDetail)
async def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """Get a specific contract with all its clauses."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.delete("/{contract_id}")
async def delete_contract(contract_id: str, db: Session = Depends(get_db)):
    """Delete a contract and its associated file."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Remove file from disk
    if os.path.exists(contract.file_path):
        os.remove(contract.file_path)

    # Remove from database (cascades to clauses)
    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully"}
