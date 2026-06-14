from fastapi import APIRouter, status, Response
from typing import Dict, Any
import requests
import time
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import SessionLocal
from app.monitoring.metrics_registry import metrics_registry

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
def get_health() -> Dict[str, Any]:
    """Returns basic system health status."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "timestamp": time.time()
    }

@router.get("/liveness", status_code=status.HTTP_200_OK)
def get_liveness() -> Dict[str, Any]:
    """Liveness check to verify the process is alive."""
    return {
        "status": "live",
        "timestamp": time.time()
    }

@router.get("/readiness")
def get_readiness(response: Response) -> Dict[str, Any]:
    """Readiness check to verify external dependencies are reachable."""
    checks = {
        "sqlite": False,
        "chromadb": False,
        "neo4j": False,
        "ollama": False
    }
    
    # 1. SQLite check
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        checks["sqlite"] = True
        db.close()
    except Exception as e:
        logger.error(f"SQLite health check failed: {e}")
        checks["sqlite"] = False

    # 2. ChromaDB check (instantiate local PersistentClient and test heartbeat)
    try:
        import chromadb
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        client.heartbeat()
        checks["chromadb"] = True
    except Exception as e:
        logger.error(f"ChromaDB local health check failed: {e}")
        checks["chromadb"] = False

    # 3. Neo4j check
    try:
        from app.services.graph.neo4j_service import Neo4jService
        neo4j = Neo4jService()
        if neo4j.health_check():
            checks["neo4j"] = True
    except Exception:
        checks["neo4j"] = False

    # 4. Ollama check (still needed for nomic-embed-text embeddings)
    try:
        res = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        if res.status_code == 200:
            checks["ollama"] = True
    except Exception:
        try:
            res = requests.get(settings.OLLAMA_BASE_URL, timeout=1.0)
            if res.status_code == 200 or res.status_code == 404:
                checks["ollama"] = True
        except Exception:
            checks["ollama"] = False

    # 5. Gemini check (if selected as provider)
    if settings.LLM_PROVIDER == "gemini":
        try:
            from app.services.llm.factory import LLMFactory
            provider = LLMFactory.get_provider()
            checks["gemini"] = provider.health_check()
        except Exception:
            checks["gemini"] = False

    # SQLite and ChromaDB are critical for the backend to function at all
    critical_checks = ["sqlite", "chromadb"]
    critical_ok = all(checks.get(k, False) for k in critical_checks)
    
    # If any checked dependency is offline, status is degraded rather than ready
    any_dep_offline = not all(checks.values())

    if not critical_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        status_str = "not_ready"
    elif any_dep_offline:
        status_str = "degraded"
    else:
        status_str = "ready"
        
    return {
        "status": status_str,
        "dependencies": checks,
        "timestamp": time.time()
    }

@router.get("/gemini")
def get_gemini_health() -> Dict[str, Any]:
    """Verifies Gemini API connectivity and credentials."""
    from app.services.llm.factory import LLMFactory
    logger.info("Gemini health check initiated")
    try:
        # Reset provider to ensure any API key updates in .env are picked up
        LLMFactory.reset_provider()
        provider = LLMFactory.get_provider()
        online = provider.health_check()
        return {
            "status": "online" if online else "offline",
            "model": settings.GEMINI_MODEL,
            "provider": "gemini"
        }
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "model": settings.GEMINI_MODEL,
            "provider": "gemini"
        }

@router.get("/metrics", status_code=status.HTTP_200_OK)
def get_metrics() -> Dict[str, Any]:
    """Exposes current system and agent execution metrics."""
    return metrics_registry.get_metrics_summary()
