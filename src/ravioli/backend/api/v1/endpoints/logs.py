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
    # Verify mission exists
    mission = db.query(models.Mission).filter(models.Mission.id == log_in.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    db_log = models.ExecutionLog(
        mission_id=log_in.mission_id,
        log_type=log_in.log_type,
        content=log_in.content,
        tool_name=log_in.tool_name,
        data=log_in.data
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/mission/{mission_id}", response_model=List[schemas.ExecutionLog])
def list_logs_for_mission(mission_id: UUID, db: Session = Depends(get_db)):
    """
    List all logs for a specific mission.
    """
    logs = db.query(models.ExecutionLog).filter(models.ExecutionLog.mission_id == mission_id).order_by(models.ExecutionLog.timestamp.asc()).all()
    return logs
