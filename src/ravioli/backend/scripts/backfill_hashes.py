import hashlib
import uuid
from pathlib import Path
from sqlalchemy import select, update
from ravioli.backend.core.database import SessionLocal
from ravioli.backend.core.models import UploadedFile
from ravioli.backend.core.config import settings

def calculate_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        while content := f.read(8192):
            sha256_hash.update(content)
    return sha256_hash.hexdigest()

def backfill():
    db = SessionLocal()
    try:
        # Get all files with missing hash
        query = select(UploadedFile).where(UploadedFile.file_hash == None)
        files = db.execute(query).scalars().all()
        
        print(f"Found {len(files)} files without hash.")
        
        for file_record in files:
            file_path = settings.local_data_path / "uploads" / file_record.filename
            if file_path.exists():
                file_hash = calculate_hash(file_path)
                file_record.file_hash = file_hash
                print(f"Updated hash for {file_record.filename}: {file_hash}")
            else:
                print(f"File not found on disk: {file_record.filename}")
        
        db.commit()
        print("Backfill completed.")
    except Exception as e:
        print(f"Error during backfill: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    backfill()
