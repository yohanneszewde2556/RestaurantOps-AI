"""
Health-check router.

GET /api/v1/health  →  system status + version info
"""

from fastapi import APIRouter
from app.core.responses import ok
from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


@router.get("", summary="Health check")
async def health_check():
    """
    Returns the API health status, application name, and version.
    Used by the frontend, monitoring tools, and load balancers.
    """
    return ok(
        data={
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
        }
    )
