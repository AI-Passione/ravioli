import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ravioli.backend.core.database import engine, Base
from ravioli.backend.data.oltp.session import ensure_schema

# Create tables in the specified schemas
# Note: schemas must exist before create_all is called for tables in those schemas
def init_db():
    try:
        # Ensure 'app' schema exists
        ensure_schema("app")
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")

app = FastAPI(
    title="Ravioli API",
    description="Backend API for Ravioli AI Data Warehouse",
    version="0.1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to Ravioli API", "status": "online"}

# Include v1 routers
from ravioli.backend.api.v1.api import api_router
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run("ravioli.backend.main:app", host="0.0.0.0", port=8000, reload=True)
