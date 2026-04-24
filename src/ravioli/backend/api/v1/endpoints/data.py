import shutil
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select

from ravioli.backend.core.database import get_db
from ravioli.backend.core.models import UploadedFile
from ravioli.backend.core.config import settings
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = settings.local_data_path / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported at this moment.")

    file_id = uuid.uuid4()
    extension = Path(file.filename).suffix
    internal_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / internal_filename
    
    # Generate a clean table name from the filename
    base_name = Path(file.filename).stem
    table_name = "".join(c if c.isalnum() else "_" for c in base_name).lower()
    # Add a suffix to ensure uniqueness if needed, but for now we'll overwrite
    
    try:
        # Save file to disk
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create record in Postgres
        db_file = UploadedFile(
            id=file_id,
            filename=internal_filename,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=file_path.stat().st_size,
            table_name=table_name,
            status="pending"
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Ingest into DuckDB
        try:
            row_count = duckdb_manager.ingest_csv(file_path, table_name)
            db_file.row_count = row_count
            db_file.status = "completed"
        except Exception as e:
            db_file.status = "failed"
            db_file.error_message = str(e)
        
        db.commit()
        db.refresh(db_file)
        
        return db_file
    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.get("/files")
async def list_files(db: Session = Depends(get_db)):
    query = select(UploadedFile).order_by(UploadedFile.created_at.desc())
    result = db.execute(query)
    return result.scalars().all()

@router.get("/tables")
async def list_duckdb_tables():
    try:
        return duckdb_manager.list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@router.get("/preview/{table_name}")
async def get_table_preview(table_name: str):
    try:
        # Validate table name to prevent SQL injection
        tables = duckdb_manager.list_tables()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail="Table not found")
            
        data = duckdb_manager.query(f"SELECT * FROM {table_name} LIMIT 10")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch preview: {str(e)}")
