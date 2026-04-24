from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
import pandas as pd
import asyncio
import io
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ravioli.backend.core.database import get_db
from ravioli.backend.core import models, schemas
from pathlib import Path

router = APIRouter()

@router.post("/", response_model=schemas.Analysis, status_code=status.HTTP_201_CREATED)
def create_analysis(analysis_in: schemas.AnalysisCreate, db: Session = Depends(get_db)):
    """
    Create a new analysis.
    """
    notebook = analysis_in.notebook
    if not notebook:
        notebook = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5
        }
        
    db_analysis = models.Analysis(
        title=analysis_in.title,
        description=analysis_in.description,
        analysis_metadata=analysis_in.analysis_metadata,
        notebook=notebook
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

@router.get("/", response_model=List[schemas.Analysis])
def list_analyses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all analyses.
    """
    analyses = db.query(models.Analysis).order_by(models.Analysis.created_at.desc()).offset(skip).limit(limit).all()
    return analyses

@router.get("/{analysis_id}", response_model=schemas.Analysis)
def get_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific analysis by ID.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis

@router.patch("/{analysis_id}", response_model=schemas.Analysis)
def update_analysis(analysis_id: UUID, analysis_in: schemas.AnalysisUpdate, db: Session = Depends(get_db)):
    """
    Update an analysis.
    """
    db_analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    update_data = analysis_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_analysis, field, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    """
    Delete an analysis.
    """
    db_analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not db_analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    db.delete(db_analysis)
    db.commit()
    return None

@router.post("/{analysis_id}/ask", status_code=status.HTTP_202_ACCEPTED)
def ask_question(analysis_id: UUID, question_in: schemas.QuestionCreate, db: Session = Depends(get_db)):
    """
    Submit a question to an analysis.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # 1. Create user log
    user_log = models.ExecutionLog(
        analysis_id=analysis_id,
        log_type="user_query",
        content=question_in.question
    )
    db.add(user_log)
    
    # 2. Update analysis status
    analysis.status = "running"
    
    # 3. Create mock agent response (for UI testing)
    agent_log = models.ExecutionLog(
        analysis_id=analysis_id,
        log_type="thought",
        content=f"Analyzing your question: '{question_in.question}'..."
    )
    db.add(agent_log)
    
    db.commit()
    return {"message": "Question received and processing started"}

def generate_summary(filename: str, row_count: int, col_count: int, columns: str) -> str:
    template_path = Path(__file__).parent.parent.parent.parent / "templates" / "quick_insight_template.md"
    try:
        template = template_path.read_text()
    except Exception:
        # Fallback if template is missing
        return f"Summary for {filename}: {row_count} rows, {col_count} columns."

    key_insights = f"""
- **Volume Concentration**: A significant portion of the activity is clustered around the primary dimensions.
- **Dimensional Depth**: The analysis of **{col_count}** variables shows high correlation between key performance indicators.
- **Anomaly Detection**: We found several interesting outliers that deviate from the norm.
- **Velocity Trend**: The data suggests a stable trajectory in engagement over the last observed period.
"""
    return template.format(
        filename=filename,
        row_count=row_count,
        col_count=col_count,
        columns=columns,
        key_insights=key_insights
    )

@router.post("/quick-insight", response_model=schemas.QuickInsightResponse)
async def create_quick_insight(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a CSV and get a quick mock insight.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Read the CSV to get some basic stats for the mock
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        row_count = len(df)
        col_count = len(df.columns)
        columns = ", ".join(df.columns.tolist()[:5])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    # Simulate AI processing time
    await asyncio.sleep(2)

    # Generate Summary using template
    title = f"Quick Insight: {file.filename}"
    summary = generate_summary(file.filename, row_count, col_count, columns)

    # Create the analysis record
    db_analysis = models.Analysis(
        title=title,
        description=f"Quick insight generated from {file.filename}",
        status="completed",
        result=summary,
        analysis_metadata={"type": "quick_insight", "filename": file.filename, "row_count": row_count}
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return schemas.QuickInsightResponse(
        analysis_id=db_analysis.id,
        title=title,
        summary=summary,
        stats={"rows": row_count, "cols": col_count}
    )

@router.post("/quick-insight/existing", response_model=schemas.QuickInsightResponse)
async def create_quick_insight_existing(
    request: schemas.QuickInsightExistingRequest,
    db: Session = Depends(get_db)
):
    """
    Generate quick insight from an already uploaded file.
    """
    from ravioli.backend.core.models import UploadedFile
    from sqlalchemy import select

    query = select(UploadedFile).where(UploadedFile.id == request.file_id)
    db_file = db.execute(query).scalar_one_or_none()
    
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if db_file.status != "completed":
        raise HTTPException(status_code=400, detail="File processing is not completed")

    # Get stats from DuckDB or DB record
    row_count = db_file.row_count or 0
    
    # Get columns from DuckDB
    try:
        from ravioli.backend.data.olap.duckdb_manager import duckdb_manager
        df_cols = duckdb_manager.query(f"DESCRIBE {db_file.table_name}")
        col_count = len(df_cols)
        columns = ", ".join([row['column_name'] for row in df_cols[:5]])
    except Exception as e:
        print(f"Error fetching columns: {e}")
        col_count = 0
        columns = "Unknown"

    # Simulate AI processing time
    await asyncio.sleep(1)

    # Generate Summary using template
    title = f"Quick Insight: {db_file.original_filename}"
    summary = generate_summary(db_file.original_filename, row_count, col_count, columns)

    # Create the analysis record
    db_analysis = models.Analysis(
        title=title,
        description=f"Quick insight generated from {db_file.original_filename}",
        status="completed",
        result=summary,
        analysis_metadata={"type": "quick_insight", "file_id": str(db_file.id), "row_count": row_count}
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return schemas.QuickInsightResponse(
        analysis_id=db_analysis.id,
        title=title,
        summary=summary,
        stats={"rows": row_count, "cols": col_count}
    )
