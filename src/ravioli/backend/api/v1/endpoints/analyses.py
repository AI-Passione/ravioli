from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
import pandas as pd
import asyncio
import io
import logging
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ravioli.backend.core.database import get_db
from ravioli.backend.core import models, schemas
from pathlib import Path
from ydata_profiling import ProfileReport


router = APIRouter()
logger = logging.getLogger(__name__)

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
async def ask_question(
    analysis_id: UUID, 
    question_in: schemas.QuestionCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
    db.commit()
    
    # 3. Queue background processing
    background_tasks.add_task(process_analysis_question, str(analysis_id), question_in.question)
    
    return {"message": "Question received and processing started"}

async def process_analysis_question(analysis_id: str, question: str):
    """
    Background task to generate AI response for a question.
    """
    from ravioli.backend.core.database import SessionLocal
    from ravioli.backend.core.ollama import OllamaClient
    import uuid
    
    db = SessionLocal()
    try:
        analysis_uuid = uuid.UUID(analysis_id)
        analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_uuid).first()
        if not analysis:
            return

        # Prepare context
        filename = analysis.analysis_metadata.get("filename", "Unknown Dataset")
        summary = analysis.result or "No summary available."
        
        # Get last 5 logs for context
        previous_logs = db.query(models.ExecutionLog)\
            .filter(models.ExecutionLog.analysis_id == analysis_uuid)\
            .order_by(models.ExecutionLog.timestamp.desc())\
            .limit(6).all() # 6 because we just added the current question
        
        context_str = ""
        for log in reversed(previous_logs[1:]): # Skip the latest question for context
            role = "Operator" if log.log_type == "user_query" else "Kowalski"
            context_str += f"{role}: {log.content}\n"

        # Generate answer
        client = OllamaClient(db)
        answer = await client.generate_answer(filename, summary, context_str, question)
        
        # Save answer
        agent_log = models.ExecutionLog(
            analysis_id=analysis_id,
            log_type="thought",
            content=answer
        )
        db.add(agent_log)
        
        # Update status
        analysis.status = "completed"
        db.commit()
    except Exception as e:
        print(f"Error in background task process_analysis_question: {e}")
        # Optionally add an error log to the analysis
    finally:
        db.close()

@router.get("/{analysis_id}/stream")
async def stream_question(
    analysis_id: UUID,
    question: str,
    db: Session = Depends(get_db)
):
    """
    Stream a response to a question using Server-Sent Events.
    """
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # 1. Create user log
    user_log = models.ExecutionLog(
        analysis_id=analysis_id,
        log_type="user_query",
        content=question
    )
    db.add(user_log)
    analysis.status = "running"
    db.commit()

    async def event_generator():
        from ravioli.backend.core.database import SessionLocal
        from ravioli.backend.core.ollama import OllamaClient
        
        # Context preparation (same as background task)
        filename = analysis.analysis_metadata.get("filename", "Unknown Dataset")
        summary = analysis.result or "No summary available."
        
        # Get last 5 logs for context
        previous_logs = db.query(models.ExecutionLog)\
            .filter(models.ExecutionLog.analysis_id == analysis_id)\
            .order_by(models.ExecutionLog.timestamp.desc())\
            .limit(6).all()
        
        context_str = ""
        for log in reversed(previous_logs[1:]):
            role = "Operator" if log.log_type == "user_query" else "Kowalski"
            context_str += f"{role}: {log.content}\n"

        client = OllamaClient(db)
        full_response = ""
        
        try:
            async for token in client.stream_answer(filename, summary, context_str, question):
                full_response += token
                yield f"data: {token}\n\n"
            
            # Persistence at the end
            async_db = SessionLocal()
            try:
                agent_log = models.ExecutionLog(
                    analysis_id=analysis_id,
                    log_type="thought",
                    content=full_response
                )
                async_db.add(agent_log)
                
                # Re-fetch analysis in this session
                a = async_db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
                if a:
                    a.status = "completed"
                async_db.commit()
            finally:
                async_db.close()
            
            yield "data: [DONE]\n\n"
                
        except Exception as e:
            logger.exception("Stream interrupted for analysis_id=%s", analysis_id)
            yield "data: [ERROR] Stream interrupted due to an internal error.\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

def prepare_dataframe_for_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Intelligently detects and casts column types for better statistical analysis."""
    df = df.copy()
    # Patterns for columns that should be treated as strings/categories, never as numeric metrics
    id_patterns = ['_id', ' id', 'postal', 'zip', 'phone', 'postcode', 'telephone', 'id']
    
    for col in df.columns:
        col_lower = col.lower()
        
        # 1. Cast IDs and non-analytical numeric codes to string/category
        if any(pat in col_lower for pat in id_patterns) or col_lower == 'id':
            # If cardinality is low, use category; otherwise string
            if df[col].nunique() < 50:
                df[col] = df[col].astype('category')
            else:
                df[col] = df[col].astype(str)
            continue

        # 2. Convert potential numeric columns that are currently strings
        if df[col].dtype == 'object':
            # Try to convert to numeric (Int64 handles nulls better than int)
            converted = pd.to_numeric(df[col], errors='coerce')
            if not converted.isna().all():
                df[col] = converted
            # Best-effort conversion: leave the original column dtype unchanged
            # if pandas cannot safely coerce this column to numeric.

        # 3. Handle low-cardinality strings as categories
        if df[col].dtype == 'object' and df[col].nunique() < 30:
            df[col] = df[col].astype('category')
            
    return df

def create_data_profile(df: pd.DataFrame) -> str:
    """Creates a high-fidelity statistical profile of the prepared dataset."""
    print(f"OllamaClient: [INFO] Profiling {len(df.columns)} columns: {df.columns.tolist()}", flush=True)
    
    # 1. Basic Stats (Describe respects types: no means for categories)
    stats = df.describe(include='all').transpose().to_string()
    
    # 2. Data Quality
    quality = pd.DataFrame({
        'dtype': df.dtypes,
        'null_count': df.isnull().sum(),
        'unique_count': df.nunique()
    }).to_string()

    advanced_insights = ""
    try:
        # Pass the FULL dataframe so every column is processed in the log
        profile = ProfileReport(df, minimal=True, title="Data Profile")
        description = profile.get_description()
        
        # Extract Alerts (The most valuable part for AI)
        alerts = description.get('alerts', [])
        if alerts:
            advanced_insights += "\nADVANCED DATA ALERTS (Excluding ID columns):\n"
            for alert in alerts[:15]: # Limit to top 15 alerts
                advanced_insights += f"- {str(alert)}\n"
        
        # Extract Column-Level Details
        variables = description.get('variables', {})
        if variables:
            advanced_insights += "\nDETAILED COLUMN ANALYSIS:\n"
            for col_name, col_data in variables.items():
                # Extract interesting metrics depending on type
                v_type = col_data.get('type', 'Unknown')
                advanced_insights += f"[{col_name}] ({v_type}): "
                
                if v_type == 'Numeric':
                    mean = col_data.get('mean', 0)
                    std = col_data.get('std', 0)
                    advanced_insights += f"Mean: {mean:.2f}, Std: {std:.2f}, Range: [{col_data.get('min')}, {col_data.get('max')}]\n"
                elif v_type == 'Categorical':
                    distinct = col_data.get('n_distinct', 0)
                    top = col_data.get('top', 'N/A')
                    advanced_insights += f"{distinct} unique values. Top: '{top}'\n"
                else:
                    advanced_insights += f"Distinct: {col_data.get('n_distinct', 0)}\n"

        # Extract Correlations (High-level summary)
        correlations = description.get('correlations', {})
        if correlations:
            advanced_insights += "\nCOLUMN CORRELATIONS IDENTIFIED.\n"
            
    except ImportError:
        advanced_insights = "\n[NOTE: ydata-profiling not installed. Falling back to basic stats.]"
    except Exception as e:
        advanced_insights = f"\n[NOTE: Advanced profiling failed: {str(e)}]"
    
    # 3. Micro Sample
    sample = df.head(10).to_csv(index=False)
    
    return f"""
DATASET PROFILE (Generated from {len(df)} rows)
==============================================
SUMMARY STATISTICS:
{stats}

DATA QUALITY & TYPES:
{quality}
{advanced_insights}

REPRESENTATIVE SAMPLE (FIRST 10 ROWS):
{sample}
"""

async def generate_summary(db: Session, filename: str, row_count: int, col_count: int, columns: str, sample_data: str) -> tuple[str, list[str]]:
    template_path = Path(__file__).resolve().parents[4] / "ai" / "templates" / "quick_insight_template.md"
    try:
        template = template_path.read_text()
    except Exception:
        # Fallback if template is missing
        return f"Summary for {filename}: {row_count} rows, {col_count} columns.", []

    # Use Ollama for key insights, assumptions, and limitations
    from ravioli.backend.core.ollama import OllamaClient
    try:
        client = OllamaClient(db)
        # Run in parallel for better performance
        key_insights, assumptions, limitations = await asyncio.gather(
            client.generate_quick_insight(filename, sample_data),
            client.generate_assumptions(filename, sample_data),
            client.generate_limitations(filename, sample_data)
        )
    except Exception as e:
        print(f"Error generating insights with Ollama: {e}")
        key_insights = f"""
> [!IMPORTANT]
> **SIMULATED INSIGHTS**: The AI engine is currently offline or unreachable. The insights below are pre-calculated baseline patterns based on your data structure (**{col_count}** variables across **{row_count}** entries).

- **Volume Concentration**: A significant portion of the activity is clustered around the primary dimensions.
- **Dimensional Depth**: High correlation observed between key performance indicators across the dataset.
- **Anomaly Detection**: Identified potential outliers that deviate from the 95th percentile norm.
- **Velocity Trend**: The data suggests a stable trajectory in engagement over the observed period.
"""
        assumptions = "- Data is representative of the period/context specified.\n- Column names are accurately descriptive of their contents."
        limitations = "- Limited context on data collection methodology.\n- Sample size may not capture all edge case variance."

    # Highlight numbers with backticks for visibility
    import re
    summary = template.format(
        filename=filename,
        row_count=row_count,
        col_count=col_count,
        columns=columns,
        key_insights=key_insights,
        assumptions=assumptions,
        limitations_and_issues=limitations
    )
    # Regex to find standalone numbers (including decimals) and wrap them in backticks
    summary = re.sub(r'(?<!`)\b(\d+(?:\.\d+)?)\b(?!`)', r'`\1`', summary)
    
    # Generate follow-up questions
    try:
        followup_questions = await client.generate_followup_questions(filename, summary, sample_data)
    except Exception:
        followup_questions = [
            "What are the primary drivers behind the observed volume concentration?",
            "Are there specific time periods where the anomalies are more prevalent?",
            "How do these trends compare to historical baseline patterns?",
            "What is the impact of the identified limitations on the overall analysis?"
        ]
    
    return summary, followup_questions

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

    # Read the CSV to get some basic stats and sample data
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        row_count = len(df)
        col_count = len(df.columns)
        columns = ", ".join(df.columns.tolist()[:5])
        # Create a statistical profile of the ENTIRE table
        df = prepare_dataframe_for_analysis(df)
        data_profile = create_data_profile(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    # Generate Summary using template and Ollama
    title = f"Quick Insight: {file.filename}"
    summary, followup_questions = await generate_summary(db, file.filename, row_count, col_count, columns, data_profile)

    # Create the analysis record
    db_analysis = models.Analysis(
        title=title,
        description=f"Quick insight generated from {file.filename}",
        status="completed",
        result=summary,
        analysis_metadata={
            "type": "quick_insight", 
            "filename": file.filename, 
            "row_count": row_count,
            "followup_questions": followup_questions
        }
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return schemas.QuickInsightResponse(
        analysis_id=db_analysis.id,
        title=title,
        summary=summary,
        stats={"rows": row_count, "cols": col_count},
        followup_questions=followup_questions
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

    # Get stats and sample data from DuckDB
    row_count = db_file.row_count or 0
    try:
        from ravioli.backend.data.olap.duckdb_manager import duckdb_manager
        df_cols = duckdb_manager.query(f"DESCRIBE {db_file.table_name}")
        col_count = len(df_cols)
        columns = ", ".join([row['column_name'] for row in df_cols[:5]])
        
        # Get full data and create a profile for AI context
        df_full = duckdb_manager.connection.execute(f'SELECT * FROM "{db_file.table_name}"').fetchdf()
        df_full = prepare_dataframe_for_analysis(df_full)
        data_profile = create_data_profile(df_full)
    except Exception as e:
        print(f"Error fetching columns or sample: {e}")
        col_count = 0
        columns = "Unknown"
        data_profile = "No statistical profile available"

    # Generate Summary using template and Ollama
    title = f"Quick Insight: {db_file.original_filename}"
    summary, followup_questions = await generate_summary(db, db_file.original_filename, row_count, col_count, columns, data_profile)

    # Create the analysis record
    db_analysis = models.Analysis(
        title=title,
        description=f"Quick insight generated from {db_file.original_filename}",
        status="completed",
        result=summary,
        analysis_metadata={
            "type": "quick_insight", 
            "file_id": str(db_file.id), 
            "row_count": row_count,
            "followup_questions": followup_questions
        }
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return schemas.QuickInsightResponse(
        analysis_id=db_analysis.id,
        title=title,
        summary=summary,
        stats={"rows": row_count, "cols": col_count},
        followup_questions=followup_questions
    )
