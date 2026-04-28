from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from ravioli.backend.core import models, schemas
from ravioli.backend.core.database import get_db

router = APIRouter()

@router.get("/", response_model=List[schemas.KnowledgePage])
def list_knowledge_pages(db: Session = Depends(get_db)):
    """List all knowledge pages."""
    return db.query(models.KnowledgePage).order_by(models.KnowledgePage.updated_at.desc()).all()

@router.post("/", response_model=schemas.KnowledgePage, status_code=status.HTTP_201_CREATED)
def create_knowledge_page(page: schemas.KnowledgePageCreate, db: Session = Depends(get_db)):
    """Create a new knowledge page."""
    db_page = models.KnowledgePage(**page.model_dump())
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

@router.get("/{page_id}", response_model=schemas.KnowledgePage)
def get_knowledge_page(page_id: UUID, db: Session = Depends(get_db)):
    """Get a knowledge page by ID."""
    page = db.query(models.KnowledgePage).filter(models.KnowledgePage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    return page

@router.patch("/{page_id}", response_model=schemas.KnowledgePage)
def update_knowledge_page(page_id: UUID, page_update: schemas.KnowledgePageUpdate, db: Session = Depends(get_db)):
    """Update a knowledge page."""
    db_page = db.query(models.KnowledgePage).filter(models.KnowledgePage.id == page_id).first()
    if not db_page:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    
    update_data = page_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_page, key, value)
    
    db.commit()
    db.refresh(db_page)
    return db_page

@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_page(page_id: UUID, db: Session = Depends(get_db)):
    """Delete a knowledge page."""
    page = db.query(models.KnowledgePage).filter(models.KnowledgePage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Knowledge page not found")
    
    db.delete(page)
    db.commit()
    return None
