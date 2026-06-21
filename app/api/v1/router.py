from fastapi import APIRouter
from app.api.v1.endpoints import health, missions, replan, geo, targets

router = APIRouter()
router.include_router(health.router)
router.include_router(missions.router, prefix="/missions")
router.include_router(replan.router, prefix="/ai")
router.include_router(geo.router, prefix="/geo")
router.include_router(targets.router, prefix="/targets")
