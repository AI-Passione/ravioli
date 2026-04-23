from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ravioli.backend.core.database import get_db
from ravioli.backend.core import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.ExecutionLog, status_code=status.HTTP_201_CREATED)
def create_log(log_in: schemas.ExecutionLogCreate, db: Session = Depends(get_db)):
    """
    Create a new execution log entry.
    """
    # Verify analysis exists
    analysis = db.query(models.Analysis).filter(models.Analysis.id == log_in.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    db_log = models.ExecutionLog(
        analysis_id=log_in.analysis_id,
        log_type=log_in.log_type,
        content=log_in.content,
        tool_name=log_in.tool_name,
        data=log_in.data
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/analysis/{analysis_id}", response_model=List[schemas.ExecutionLog])
def list_logs_for_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    """
    List all logs for a specific analysis.
    """
    logs = db.query(models.ExecutionLog).filter(models.ExecutionLog.analysis_id == analysis_id).order_by(models.ExecutionLog.timestamp.asc()).all()
    return logs
