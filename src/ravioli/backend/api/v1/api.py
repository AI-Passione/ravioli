from fastapi import APIRouter
from ravioli.backend.api.v1.endpoints import analyses, logs, data, settings

api_router = APIRouter()
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
