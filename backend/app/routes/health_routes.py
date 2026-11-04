from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.models.schemas import HealthCheckResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthCheckResponse, summary="System Health Check")
def health_check():
    """Verify application uptime and active AI services."""
    deps = {
        "groq_api": "configured" if bool(settings.groq_api_key) else "missing",
        "vision_model": settings.groq_model_extraction,
        "chat_model": settings.groq_model_chat
    }
    status = "healthy" if settings.groq_api_key else "degraded"
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.app_version,
        dependencies=deps
    )
