from fastapi import APIRouter

from app.models.schemas import HealthResponse
from app.core.session_manager import session_manager
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        HealthResponse with service status and version
    """
    return HealthResponse(
        status="healthy",
        version=settings.api_version
    )


@router.get("/sessions/count")
async def get_active_sessions_count():
    """
    Get the number of active sessions (for monitoring)
    
    Returns:
        Dict with active session count
    """
    return {
        "active_sessions": session_manager.get_active_sessions_count()
    }
