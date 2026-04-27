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

# Import all models so SQLAlchemy registers them with Base.metadata before create_all.
# These imports are intentional side-effects; the linter hint about "unused" is incorrect.
import ravioli.backend.core.models  # noqa: F401

# Create tables in the specified schemas
# Note: schemas must exist before create_all is called for tables in those schemas
def init_db():
    try:
        # Ensure 'app' schema exists
        ensure_schema("app")
        # Create all tables (new tables only; existing tables are not modified)
        Base.metadata.create_all(bind=engine)
        # Idempotent column migrations for tables that already exist
        _migrate_columns()
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def _migrate_columns():
    """Add new columns to existing tables using IF NOT EXISTS (idempotent)."""
    from sqlalchemy import text
    migrations = [
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS assumptions TEXT",
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS limitations TEXT",
        "ALTER TABLE app.insights ADD COLUMN IF NOT EXISTS metadata JSONB",
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
