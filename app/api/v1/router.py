from fastapi import APIRouter
from app.api.v1.endpoints import health, missions

router = APIRouter()
router.include_router(health.router)
router.include_router(missions.router, prefix="/missions")
