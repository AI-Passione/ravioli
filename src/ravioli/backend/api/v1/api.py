from fastapi import APIRouter
from ravioli.backend.api.v1.endpoints import analyses, analysis_logs, data, settings, insights, knowledge

api_router = APIRouter()
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
api_router.include_router(analysis_logs.router, prefix="/analysis-logs", tags=["analysis-logs"])
api_router.include_router(data.router, prefix="/data", tags=["data"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
