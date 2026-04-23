from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ravioli.backend.core.database import get_db
from ravioli.backend.core import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.Mission, status_code=status.HTTP_201_CREATED)
def create_mission(mission_in: schemas.MissionCreate, db: Session = Depends(get_db)):
    """
    Create a new mission.
    """
    db_mission = models.Mission(
        title=mission_in.title,
        description=mission_in.description,
        mission_metadata=mission_in.mission_metadata
    )
    db.add(db_mission)
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.get("/", response_model=List[schemas.Mission])
def list_missions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all missions.
    """
    missions = db.query(models.Mission).offset(skip).limit(limit).all()
    return missions

@router.get("/{mission_id}", response_model=schemas.Mission)
def get_mission(mission_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific mission by ID.
    """
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.patch("/{mission_id}", response_model=schemas.Mission)
def update_mission(mission_id: UUID, mission_in: schemas.MissionUpdate, db: Session = Depends(get_db)):
    """
    Update a mission.
    """
    db_mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    update_data = mission_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_mission, field, value)
    
    db.commit()
    db.refresh(db_mission)
    return db_mission

@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a mission.
    """
    db_mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    db.delete(db_mission)
    db.commit()
    return None

@router.post("/{mission_id}/ask", status_code=status.HTTP_202_ACCEPTED)
def ask_question(mission_id: UUID, question_in: schemas.QuestionCreate, db: Session = Depends(get_db)):
    """
    Submit a question to a mission.
    """
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    # 1. Create user log
    user_log = models.ExecutionLog(
        mission_id=mission_id,
        log_type="user_query",
        content=question_in.question
    )
    db.add(user_log)
    
    # 2. Update mission status
    mission.status = "running"
    
    # 3. Create mock agent response (for UI testing)
    agent_log = models.ExecutionLog(
        mission_id=mission_id,
        log_type="thought",
        content=f"Analyzing your question: '{question_in.question}'..."
    )
    db.add(agent_log)
    
    db.commit()
    return {"message": "Question received and processing started"}
