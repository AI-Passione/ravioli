from fastapi import APIRouter
from ravioli.backend.api.v1.endpoints import analyses, logs

api_router = APIRouter()
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
