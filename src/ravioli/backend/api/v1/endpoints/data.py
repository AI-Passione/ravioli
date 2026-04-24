import re
import shutil
import uuid
import hashlib
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import select

from ravioli.backend.core import schemas
from ravioli.backend.core.database import get_db
from ravioli.backend.core.config import settings
from ravioli.backend.core.models import UploadedFile
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = settings.local_data_path / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def calculate_hash(file: UploadFile) -> str:
    sha256_hash = hashlib.sha256()
    # Read in chunks to avoid memory issues
    while content := await file.read(8192):
        sha256_hash.update(content)
    await file.seek(0)  # Important: reset pointer for subsequent reads
    return sha256_hash.hexdigest()

@router.post("/upload", response_model=schemas.UploadedFile)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported at this moment.")

    # Generate hash to check for duplicates
    file_hash = await calculate_hash(file)
    
    # Check if file with same hash already exists
    query = select(UploadedFile).where(UploadedFile.file_hash == file_hash)
    existing_file = db.execute(query).scalar_one_or_none()
    
    if existing_file:
        # If it exists and was successful, we can just return it
        if existing_file.status == "completed":
            # Inform the user it was a duplicate
            existing_file.is_duplicate = True
            return existing_file
        else:
            # If it failed or is pending, we proceed to retry
            pass

    file_id = uuid.uuid4()
    extension = Path(file.filename).suffix
    internal_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / internal_filename
    
    # Generate a clean table name from the filename
    base_name = Path(file.filename).stem
    table_name = "".join(c if c.isalnum() else "_" for c in base_name).lower()
    
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
            file_hash=file_hash,
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

@router.get("/files", response_model=List[schemas.UploadedFile])
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
    if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
        raise HTTPException(status_code=400, detail="Invalid table name")

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

@router.delete("/files/{file_id}")
async def delete_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    # 1. Fetch record
    db_file = db.execute(select(UploadedFile).where(UploadedFile.id == file_id)).scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # 2. Drop table from DuckDB
        if db_file.table_name:
            duckdb_manager.connection.execute(f"DROP TABLE IF EXISTS {db_file.table_name}")
            
        # 3. Delete physical file
        file_path = UPLOAD_DIR / db_file.filename
        if file_path.exists():
            file_path.unlink()
            
        # 4. Delete Postgres record
        db.delete(db_file)
        db.commit()
        
        return {"status": "success", "message": "File and associated data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.patch("/files/{file_id}", response_model=schemas.UploadedFile)
async def update_file(
    file_id: uuid.UUID,
    file_update: schemas.UploadedFileUpdate,
    db: Session = Depends(get_db)
):
    db_file = db.execute(select(UploadedFile).where(UploadedFile.id == file_id)).scalar_one_or_none()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_update.description is not None:
        db_file.description = file_update.description
        
    try:
        db.commit()
        db.refresh(db_file)
        return db_file
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")
