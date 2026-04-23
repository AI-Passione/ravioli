from fastapi import APIRouter
from ravioli.backend.api.v1.endpoints import missions, logs

api_router = APIRouter()
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
