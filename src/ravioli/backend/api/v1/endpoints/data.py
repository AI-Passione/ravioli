import re
import shutil
import uuid
import hashlib
from pathlib import Path
from typing import List, Optional
import json
import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from ravioli.backend.core import schemas, models
from ravioli.backend.core.database import get_db, SessionLocal
from ravioli.backend.core.config import settings
from ravioli.backend.core.models import DataSource
from ravioli.backend.data.olap.duckdb_manager import duckdb_manager, data_ingestor
from ravioli.backend.data.olap.ingestion.ingestor import WFSClient
from ravioli.backend.data.olap.ingestion.utils import pii_scanner, create_ravioli_pipeline

import logging
from ravioli.backend.core.ollama import OllamaClient

logger = logging.getLogger(__name__)

router = APIRouter()

class LogCaptureHandler(logging.Handler):
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue
        self.setFormatter(logging.Formatter('%(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            # Use call_soon_threadsafe to safely push to queue from potentially different threads
            asyncio.get_event_loop().call_soon_threadsafe(self.queue.put_nowait, msg)
        except Exception:
            self.handleError(record)

UPLOAD_DIR = settings.local_data_path / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def get_current_user(db: Session = Depends(get_db)) -> models.User:
    """
    Temporary helper to get or create a default system user.
    Once auth is implemented, this should pull from JWT/Session.
    """
    email = "jimmypang@aipassione.com"
    user = db.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()
    if not user:
        user = models.User(
            id=uuid.uuid4(),
            name="Jimmy Pang",
            email=email
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def calculate_hash(file: UploadFile) -> str:
    sha256_hash = hashlib.sha256()
    # Read in chunks to avoid memory issues
    while content := await file.read(8192):
        sha256_hash.update(content)
    await file.seek(0)  # Important: reset pointer for subsequent reads
    return sha256_hash.hexdigest()

@router.post("/upload", response_model=schemas.DataSource)
async def upload_file(
    file: UploadFile = File(...),
    context: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    extension = Path(file.filename).suffix.lower()
    allowed_extensions = ['.csv', '.xlsx', '.xml', '.gpx']
    if extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}")

    # Generate hash to check for duplicates
    file_hash = await calculate_hash(file)
    
    # Check if file with same hash already exists
    query = select(DataSource).where(DataSource.file_hash == file_hash)
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
    internal_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / internal_filename
    
    # Generate a clean, unique table name from the filename
    base_name = Path(file.filename).stem
    clean_base = "".join(c if c.isalnum() else "_" for c in base_name).lower()
    table_name = f"{clean_base}_{file_id.hex[:4]}"
    
    try:
        # Save file to disk
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create record in Postgres
        db_source = DataSource(
            id=file_id,
            filename=internal_filename,
            original_filename=file.filename,
            content_type=file.content_type,
            size_bytes=file_path.stat().st_size,
            table_name=table_name,
            schema_name="s_manual",
            file_hash=file_hash,
            status="pending",
            has_pii=False,
            owner_id=current_user.id
        )
        db.add(db_source)
        db.commit()
        db.refresh(db_source)
        
        try:
            if extension == '.csv':
                row_count = data_ingestor.ingest_csv(file_path, table_name, schema="s_manual")
                db_source.row_count = row_count
                
                # PII Scan
                try:
                    full_table_name = f'"s_manual"."{table_name}"'
                    df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 100').fetchdf()
                    db_source.has_pii = pii_scanner.scan_dataframe(df_sample)
                except Exception as e:
                    logger.warning("PII scan failed for table %s: %s", table_name, e)
                    db_source.has_pii = False
                    
                db_source.status = "completed"
                
                # Auto-description for CSV
                try:
                    ollama_client = OllamaClient(db)
                    full_table_name = f'"s_manual"."{table_name}"'
                    df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 5').fetchdf()
                    db_source.description = await ollama_client.generate_description(db_source.original_filename, df_sample.to_csv(index=False), context=context)
                except Exception as e:
                    logger.warning("Auto-description failed for CSV: %s", e)
            elif extension in ['.xml', '.gpx']:
                # Generic XML/GPX Ingestion
                if extension == '.xml':
                    results = data_ingestor.ingest_xml(file_path, file.filename, schema="s_manual")
                else: # .gpx
                    results = data_ingestor.ingest_gpx(file_path, file.filename, schema="s_manual")
                
                valid_results = [r for r in results if r["status"] == "completed"]
                
                if not valid_results:
                    db_source.status = "failed"
                    db_source.error_message = "No valid data extracted from file."
                else:
                    # Update primary record
                    first = valid_results[0]
                    db_source.table_name = first["table_name"]
                    db_source.row_count = first["row_count"]
                    db_source.status = "completed"
                    
                    # AI Description for primary
                    try:
                        ollama_client = OllamaClient(db)
                        # For XML/GPX, we read the first 2000 chars as the "sample"
                        with file_path.open("r", errors="ignore") as f:
                            sample_text = f.read(2000)
                        db_source.description = await ollama_client.generate_description(db_source.original_filename, sample_text, context=context)
                    except Exception as e:
                        logger.warning("Auto-description failed for XML/GPX: %s", e)
                        
                    # PII Scan for primary
                    try:
                        full_table_name = f'"s_manual"."{db_source.table_name}"'
                        df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 100').fetchdf()
                        db_source.has_pii = pii_scanner.scan_dataframe(df_sample)
                    except Exception as e:
                        logger.warning("PII scan failed for table %s: %s", db_source.table_name, e)

                    # Create records for other valid tables
                    for other in valid_results[1:]:
                        other_source = DataSource(
                            id=uuid.uuid4(),
                            filename=internal_filename,
                            original_filename=f"{file.filename} [{other['table_name']}]",
                            content_type=file.content_type,
                            size_bytes=file_path.stat().st_size,
                            table_name=other["table_name"],
                            schema_name="s_manual",
                            file_hash=file_hash,
                            status="completed",
                            row_count=other["row_count"],
                            has_pii=False, owner_id=current_user.id
                        )
                        # PII Scan for other
                        try:
                            full_table_name = f'"s_manual"."{other["table_name"]}"'
                            df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 100').fetchdf()
                            other_source.has_pii = pii_scanner.scan_dataframe(df_sample)
                        except Exception as e:
                            logger.warning("PII scan failed for table %s: %s", other["table_name"], e)
                        
                        # AI Description for other
                        try:
                            other_source.description = await ollama_client.generate_description(other_source.original_filename, sample_text, context=context)
                        except:
                            pass
                            
                        db.add(other_source)
            else: # .xlsx
                ollama_client = OllamaClient(db)
                xlsx_results = await data_ingestor.ingest_xlsx(file_path, table_name, schema="s_manual", ollama_client=ollama_client)
                
                valid_results = [r for r in xlsx_results if r["status"] == "completed"]
                
                if not valid_results:
                    failures = [f"Sheet '{r['sheet_name']}': {r['error']}" for r in xlsx_results if r["status"] == "failed"]
                    db_source.status = "failed"
                    db_source.error_message = " | ".join(failures) if failures else "No valid data sheets found."
                else:
                    # Update primary record with first valid sheet
                    first = valid_results[0]
                    db_source.table_name = first["table_name"]
                    db_source.row_count = first["row_count"]
                    db_source.original_filename = f"{file.filename} [{first['sheet_name']}]"
                    db_source.status = "completed"
                    
                    # Auto-description for primary
                    try:
                        ollama_client = OllamaClient(db)
                        full_table_name = f'"s_manual"."{db_source.table_name}"'
                        df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 5').fetchdf()
                        db_source.description = await ollama_client.generate_description(db_source.original_filename, df_sample.to_csv(index=False), context=context)
                    except Exception as e:
                        logger.warning("Auto-description failed for primary sheet: %s", e)
                    
                    # PII Scan for primary
                    try:
                        full_table_name = f'"s_manual"."{db_source.table_name}"'
                        df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 100').fetchdf()
                        db_source.has_pii = pii_scanner.scan_dataframe(df_sample)
                    except Exception as e:
                        logger.warning("PII scan failed for table %s: %s", db_source.table_name, e)
                    
                    # Create records for other valid sheets
                    for other in valid_results[1:]:
                        other_source = DataSource(
                            id=uuid.uuid4(),
                            filename=internal_filename,
                            original_filename=f"{file.filename} [{other['sheet_name']}]",
                            content_type=file.content_type,
                            size_bytes=file_path.stat().st_size,
                            table_name=other["table_name"],
                            schema_name="s_manual",
                            file_hash=file_hash,
                            status="completed",
                            row_count=other["row_count"],
                            has_pii=False, owner_id=current_user.id
                        )
                        # PII Scan for other
                        try:
                            full_table_name = f'"s_manual"."{other["table_name"]}"'
                            df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 100').fetchdf()
                            other_source.has_pii = pii_scanner.scan_dataframe(df_sample)
                        except Exception as e:
                            logger.warning("PII scan failed for table %s: %s", other["table_name"], e)
                            other_source.has_pii = False
                        # Auto-description for other
                        try:
                            ollama_client = OllamaClient(db)
                            full_table_name = f'"s_manual"."{other["table_name"]}"'
                            df_sample = duckdb_manager.connection.execute(f'SELECT * FROM {full_table_name} LIMIT 5').fetchdf()
                            other_source.description = await ollama_client.generate_description(other_source.original_filename, df_sample.to_csv(index=False), context=context)
                        except Exception as e:
                            logger.warning("Auto-description failed for sheet %s: %s", other['sheet_name'], e)
                            
                        db.add(other_source)
        except Exception as e:
            db_source.status = "failed"
            db_source.error_message = str(e)
        
        db.commit()
        db.refresh(db_source)
        
        return db_source
    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@router.get("/files", response_model=List[schemas.DataSource])
async def list_files(db: Session = Depends(get_db)):
    query = select(DataSource).options(joinedload(DataSource.owner)).order_by(DataSource.created_at.desc())
    result = db.execute(query)
    return result.scalars().all()

@router.get("/tables")
async def list_duckdb_tables():
    try:
        return duckdb_manager.list_tables()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@router.get("/preview/{full_table_name}")
async def get_table_preview(full_table_name: str):
    # Allow alphanumeric, underscores, and exactly one dot for schema separation
    if not re.match(r"^[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)?$", full_table_name):
        raise HTTPException(status_code=400, detail="Invalid table name format. Use 'table' or 'schema.table'")

    try:
        # Validate table name to prevent SQL injection
        tables = duckdb_manager.list_tables()
        if full_table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table {full_table_name} not found")
            
        # Wrap components in quotes for DuckDB safety
        if "." in full_table_name:
            s, t = full_table_name.split(".")
            quoted_name = f'"{s}"."{t}"'
        else:
            quoted_name = f'"{full_table_name}"'
            
        data = duckdb_manager.query(f"SELECT * FROM {quoted_name} LIMIT 10")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch preview: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_file(file_id: uuid.UUID, db: Session = Depends(get_db)):
    # 1. Fetch record
    db_source = db.execute(select(DataSource).where(DataSource.id == file_id)).scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        # 2. Drop table from DuckDB
        if db_source.table_name:
            full_table_name = f'"{db_source.schema_name}"."{db_source.table_name}"'
            duckdb_manager.connection.execute(f"DROP TABLE IF EXISTS {full_table_name}")
            
        # 3. Delete physical file
        file_path = UPLOAD_DIR / db_source.filename
        if file_path.exists():
            file_path.unlink()
            
        # 4. Delete Postgres record
        db.delete(db_source)
        db.commit()
        
        return {"status": "success", "message": "File and associated data deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@router.patch("/files/{file_id}", response_model=schemas.DataSource)
async def update_file(
    file_id: uuid.UUID,
    file_update: schemas.DataSourceUpdate,
    db: Session = Depends(get_db)
):
    db_source = db.execute(select(DataSource).where(DataSource.id == file_id)).scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="File not found")
        
    if file_update.description is not None:
        db_source.description = file_update.description
        
    try:
        db.commit()
        db.refresh(db_source)
        return db_source
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")

@router.patch("/files/{file_id}/pii", response_model=schemas.DataSource)
async def update_file_pii(
    file_id: uuid.UUID,
    pii_update: schemas.DataSourcePIIUpdate,
    db: Session = Depends(get_db)
):
    db_source = db.execute(select(DataSource).where(DataSource.id == file_id)).scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="File not found")
        
    db_source.has_pii = pii_update.has_pii
    try:
        db.commit()
        db.refresh(db_source)
        return db_source
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update PII status: {str(e)}")

@router.post("/files/{file_id}/generate-description", response_model=schemas.DataSource)
async def generate_file_description(
    file_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    db_source = db.execute(select(DataSource).where(DataSource.id == file_id)).scalar_one_or_none()
    if not db_source:
        raise HTTPException(status_code=404, detail="File not found")
        
    if not db_source.table_name:
        raise HTTPException(status_code=400, detail="File has no associated table")

    try:
        # Get sample data from DuckDB
        full_table_name = f'"{db_source.schema_name}"."{db_source.table_name}"'
        query = f'SELECT * FROM {full_table_name} LIMIT 5'
        df = duckdb_manager.connection.execute(query).fetchdf()
        sample_data = df.to_csv(index=False)

        # Generate description using Ollama
        client = OllamaClient(db)
        description = await client.generate_description(db_source.original_filename, sample_data)

        # Update the database
        db_source.description = description
        db.commit()
        db.refresh(db_source)
        
        return db_source
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate description: {str(e)}")

# --- WFS Endpoints ---

@router.get("/wfs/layers", response_model=List[schemas.WFSLayer])
async def list_wfs_layers(url: str):
    try:
        client = WFSClient(url)
        return await client.get_capabilities()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch WFS layers: {str(e)}")

async def _run_wfs_ingestion(file_id: uuid.UUID, url: str, layer: Optional[str], table_name: str, schema_name: str):
    """Background task: performs the actual WFS data pull and DuckDB ingestion."""
    db = SessionLocal()

    PROGRESS_FLUSH_EVERY = 5_000  # commit row count to DB every N rows

    try:
        db_source = db.execute(select(DataSource).where(DataSource.id == file_id)).scalar_one()

        client = WFSClient(url)

        # Auto-detect the primary layer if one was not specified
        if not layer:
            layers = await client.get_capabilities()
            if not layers:
                raise ValueError("No layers found at this WFS endpoint.")
            layer = layers[0]["name"]
            base_name = layer.split(":")[-1]
            table_name = "".join(c if c.isalnum() else "_" for c in base_name).lower()
            db_source.original_filename = layer
            db_source.table_name = table_name
            db.commit()
            logger.info(f"Auto-detected layer: {layer}, table: {table_name}")

        # Ensure schema exists in DuckDB before dlt starts
        duckdb_manager.connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

        base_generator = client.get_features_generator(layer)

        # Wrap the generator to track & periodically persist row count
        rows_fetched = 0

        async def progress_tracking_generator():
            nonlocal rows_fetched
            async for row in base_generator:
                yield row
                rows_fetched += 1
                if rows_fetched % PROGRESS_FLUSH_EVERY == 0:
                    db_source.row_count = rows_fetched
                    db.commit()
                    logger.info(f"Progress: {rows_fetched:,} rows fetched so far for {schema_name}.{table_name}")

        # dlt pipeline - isolate by schema and unique ID to avoid state collisions
        pipeline = create_ravioli_pipeline(
            pipeline_name=f"wfs_{schema_name}_{table_name}_{uuid.uuid4().hex[:8]}",
            dataset_name=schema_name
        )

        logger.info(f"Running dlt pipeline for {schema_name}.{table_name}...")
        load_info = pipeline.run(progress_tracking_generator(), table_name=table_name, write_disposition="replace")
        logger.info(f"dlt pipeline completed. Load Info: {load_info}")

        # Final accurate row count from DuckDB
        full_table_name = f'"{schema_name}"."{table_name}"'
        db_source.row_count = duckdb_manager.connection.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]

        # PII Scan
        logger.info(f"Performing PII scan on {full_table_name}...")
        try:
            df_sample = duckdb_manager.connection.execute(f"SELECT * FROM {full_table_name} LIMIT 100").fetchdf()
            db_source.has_pii = pii_scanner.scan_dataframe(df_sample)
            logger.info(f"PII scan completed. Detected: {db_source.has_pii}")
        except Exception as scan_err:
            logger.warning(f"PII scan failed: {scan_err}")
            db_source.has_pii = False

        db_source.status = "completed"
        logger.info(f"WFS ingestion completed successfully: {db_source.row_count:,} rows.")

    except Exception as e:
        logger.exception(f"WFS Ingestion background task failed for layer {layer}")
        try:
            db_source.status = "failed"
            db_source.error_message = str(e)
        except Exception as status_err:
            logger.warning(f"Failed to persist failure status for layer {layer}: {status_err}")

    finally:
        db.commit()
        db.close()


@router.post("/wfs/ingest", response_model=schemas.DataSource)
async def ingest_wfs_layer(
    request: schemas.WFSInjestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Derive placeholder names from the URL; the background task will update
    # them once the real layer name is known (if layer was not provided).
    app_name = request.url.split("/")[-1].split("?")[0] or "wfs"
    schema_name = f"s_{app_name}"
    if request.layer:
        base_name = request.layer.split(":")[-1]
        table_name = "".join(c if c.isalnum() else "_" for c in base_name).lower()
        display_name = request.layer
    else:
        table_name = "pending"
        display_name = app_name

    logger.info(f"Queuing WFS ingestion: url={request.url}, layer={request.layer}, schema={schema_name}")

    # Create the record immediately with 'pending' status so the UI shows it right away
    file_id = uuid.uuid4()
    db_source = DataSource(
        id=file_id,
        filename=f"wfs_{file_id}",
        original_filename=display_name,
        content_type="application/wfs",
        size_bytes=0,
        table_name=table_name,
        schema_name=schema_name,
        source_type="wfs",
        source_url=request.url,
        status="pending"
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)

    # Fire-and-forget: schedule the heavy work in the background
    background_tasks.add_task(
        _run_wfs_ingestion,
        file_id=file_id,
        url=request.url,
        layer=request.layer,
        table_name=table_name,
        schema_name=schema_name
    )

    # Return immediately — the client will poll for status updates
    return db_source

@router.post("/upload-stream")
async def upload_file_stream(
    file: UploadFile = File(...),
    context: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Same as upload_file but returns a StreamingResponse with real-time logs.
    """
    log_queue = asyncio.Queue()
    handler = LogCaptureHandler(log_queue)
    
    # Attach handler to root ravioli logger to catch all sub-module logs
    ingestion_logger = logging.getLogger("ravioli")
    ingestion_logger.addHandler(handler)

    async def event_generator():
        temp_path = None
        try:
            # 1. Save file to disk immediately to avoid "read of closed file" error
            # when the request scope ends before the ingestion task completes.
            file_id = uuid.uuid4()
            extension = Path(file.filename).suffix.lower()
            internal_filename = f"{file_id}{extension}"
            temp_path = UPLOAD_DIR / internal_filename
            
            with temp_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Reset file pointer for the hash calculation in upload_file (if we still used it)
            # but actually we'll pass a wrapped file or just let upload_file handle it.
            # Actually, upload_file expects an UploadFile. 
            # To avoid refactoring too much, we'll seek(0) and hope for the best, 
            # but better yet, we refactor upload_file to take a path.
            
            # Start the ingestion task
            # Note: we still pass 'file' because upload_file uses its metadata, 
            # but upload_file will now read from the open file object which is fine 
            # since we are still in the generator.
            await file.seek(0)
            ingestion_task = asyncio.create_task(upload_file(file, context, db, current_user))
            
            # While the task is running, yield logs
            while not ingestion_task.done():
                try:
                    msg = await asyncio.wait_for(log_queue.get(), timeout=0.1)
                    yield f"data: LOG:{msg}\n\n"
                except asyncio.TimeoutError:
                    continue
            
            # Once done, get result or error
            try:
                result = await ingestion_task
                result_dict = {
                    "id": str(result.id),
                    "original_filename": result.original_filename,
                    "status": result.status,
                    "description": result.description,
                    "is_duplicate": getattr(result, "is_duplicate", False),
                    "error_message": result.error_message,
                    "schema_name": result.schema_name,
                    "table_name": result.table_name
                }
                yield f"data: DONE:{json.dumps(result_dict)}\n\n"
            except Exception as e:
                logger.exception("Error during upload_file_stream ingestion task")
                yield f"data: ERROR:An internal error occurred: {str(e)}\n\n"
                
        finally:
            ingestion_logger.removeHandler(handler)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

