"""
AXIOM Health Check
Nexxon National | Unclassified

Required for Kubernetes liveness/readiness probes
and DoD infrastructure monitoring.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    timestamp: str
    classification: str


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    System health check.
    Returns current status, version, and classification level.
    """
    return HealthResponse(
        status="operational",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc).isoformat(),
        classification="UNCLASSIFIED",
    )
