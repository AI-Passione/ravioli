import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from ravioli.backend.core.database import engine, Base
from ravioli.backend.data.oltp.session import ensure_schema

# Create tables in the specified schemas
# Note: schemas must exist before create_all is called for tables in those schemas
def init_db():
    from ravioli.backend.core import models # Ensure models are registered
    try:
        # Ensure 'app' schema exists
        ensure_schema("app")
        # Create all tables (new tables only; existing tables are not modified)
        Base.metadata.create_all(bind=engine)
        # Idempotent column migrations for tables that already exist
        _migrate_columns()
        # Seed initial data
        seed_db()
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def seed_db():
    """Create initial dummy records if they don't exist."""
    from ravioli.backend.core import models
    from ravioli.backend.core.database import SessionLocal
    import uuid
    
    db = SessionLocal()
    try:
        email = "jimmypang@aipassione.com"
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            user = models.User(
                id=uuid.uuid4(),
                name="Jimmy Pang",
                email=email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Seeded dummy user: {user.name}")
        
        # Backfill: Populate owner_id for all existing data sources that are NULL
        updated_count = db.query(models.DataSource).filter(models.DataSource.owner_id == None).update({models.DataSource.owner_id: user.id})
        if updated_count > 0:
            db.commit()
            print(f"Backfilled {updated_count} data sources with owner_id: {user.name}")
            
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()

def _migrate_columns():
    """Add new columns to existing tables using IF NOT EXISTS (idempotent)."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS assumptions TEXT",
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS limitations TEXT",
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS insight_metadata JSONB",
        "ALTER TABLE app.knowledge_pages ADD COLUMN IF NOT EXISTS icon JSONB",
        "ALTER TABLE app.knowledge_pages ADD COLUMN IF NOT EXISTS cover JSONB",
        "ALTER TABLE app.knowledge_pages ADD COLUMN IF NOT EXISTS properties JSONB",
        "ALTER TABLE app.knowledge_pages ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES app.knowledge_pages(id)",
        "ALTER TABLE app.data_sources ADD COLUMN IF NOT EXISTS owner_id UUID REFERENCES app.users(id)",
        # Safe type migration for content: wraps existing text in a paragraph block
        "ALTER TABLE app.knowledge_pages ALTER COLUMN content TYPE JSONB USING CASE WHEN content IS NULL THEN '[]'::JSONB WHEN content::text ~ '^[\\[\\{]' THEN content::JSONB ELSE jsonb_build_array(jsonb_build_object('type', 'paragraph', 'paragraph', jsonb_build_object('rich_text', jsonb_build_array(jsonb_build_object('type', 'text', 'text', jsonb_build_object('content', content)))))) END",
    ]
    with engine.begin() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                print(f"Migration warning (non-fatal): {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (if needed)

app = FastAPI(
    title="Ravioli API",
    description="Backend API for Ravioli AI Data Warehouse",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Ravioli API", "status": "online"}

# Include v1 routers
from ravioli.backend.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("ravioli.backend.main:app", host="0.0.0.0", port=8000, reload=True)
