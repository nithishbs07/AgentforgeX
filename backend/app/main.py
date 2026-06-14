from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import Base, engine
from app.api.v1.api import api_router
from app.monitoring.middleware import MonitoringMiddleware
from app.monitoring.router import router as monitoring_router

def create_app() -> FastAPI:
    # 1. Initialize logging system
    setup_logging()

    # 2. Bootstrapping database schema (auto-creates tables in SQLite if they don't exist)
    Base.metadata.create_all(bind=engine)

    # 3. Initialize FastAPI instance
    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # 4. Monitoring Middleware & CORS configuration
    app.add_middleware(MonitoringMiddleware)
    
    if settings.BACKEND_CORS_ORIGINS:
        origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 5. Include routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    app.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])

    return app

app = create_app()
