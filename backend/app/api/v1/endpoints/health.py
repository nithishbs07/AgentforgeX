from fastapi import APIRouter

router = APIRouter()

@router.get("", status_code=200)
def check_health():
    """Simple API status checks for orchestration systems or frontend checks."""
    return {
        "status": "healthy",
        "service": "AgentForge-X Backend",
        "version": "1.0.0"
    }
