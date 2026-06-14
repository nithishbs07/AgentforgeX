from fastapi import APIRouter
from app.api.v1.endpoints import health, sessions, documents, chat, analytics
from app.monitoring.router import router as monitoring_router

api_router = APIRouter()

# Incorporate sub-routers into base API Router
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])


