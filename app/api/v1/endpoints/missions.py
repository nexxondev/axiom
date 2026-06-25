"""
AXIOM Missions API — Database Connected
Nexxon National | Unclassified

Full CRUD against persistent SQLite/PostgreSQL.
No more in-memory store.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.db import crud
from app.models import (
    Mission, MissionCreate, MissionUpdate,
    MissionStatus, EventType, ClassificationLevel,
)
from app.api.deps import require_staff, require_commander, require_observer
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("missions")


def _db_to_mission(db_obj) -> dict:
    return {
        "id": db_obj.id,
        "name": db_obj.name,
        "mission_type": db_obj.mission_type,
        "status": db_obj.status,
        "classification": db_obj.classification,
        "description": db_obj.description,
        "operational_area": db_obj.operational_area,
        "planned_start": db_obj.planned_start,
        "planned_end": db_obj.planned_end,
        "created_by": db_obj.created_by,
        "created_at": db_obj.created_at,
        "updated_at": db_obj.updated_at,
    }


@router.get("/", tags=["Missions"])
async def list_missions(
    current_user: TokenData = Depends(require_observer),
    db: AsyncSession = Depends(get_db),
):
    missions = await crud.get_all_missions(db)
    return [_db_to_mission(m) for m in missions]


@router.post("/", status_code=status.HTTP_201_CREATED, tags=["Missions"])
async def create_mission(
    payload: MissionCreate,
    current_user: TokenData = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    data = payload.model_dump()
    data["created_by"] = current_user.sub
    data["status"] = MissionStatus.PLANNING
    mission = await crud.create_mission(db, data)
    await crud.create_event(db, {
        "mission_id": mission.id,
        "event_type": EventType.MISSION_CREATED,
        "actor": current_user.sub,
        "summary": f"Mission '{mission.name}' created",
        "payload": {"mission_type": mission.mission_type},
    })
    logger.info("mission_created", mission_id=mission.id, name=mission.name)
    return _db_to_mission(mission)


@router.get("/{mission_id}", tags=["Missions"])
async def get_mission(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
    db: AsyncSession = Depends(get_db),
):
    mission = await crud.get_mission(db, str(mission_id))
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return _db_to_mission(mission)


@router.patch("/{mission_id}", tags=["Missions"])
async def update_mission(
    mission_id: UUID,
    payload: MissionUpdate,
    current_user: TokenData = Depends(require_staff),
    db: AsyncSession = Depends(get_db),
):
    mission = await crud.get_mission(db, str(mission_id))
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    update_data = payload.model_dump(exclude_unset=True)
    updated = await crud.update_mission(db, str(mission_id), update_data)
    if "status" in update_data:
        await crud.create_event(db, {
            "mission_id": str(mission_id),
            "event_type": EventType.MISSION_STATUS_CHANGED,
            "actor": current_user.sub,
            "summary": f"Mission status changed to {update_data['status']}",
            "payload": {"new_status": update_data["status"]},
        })
    return _db_to_mission(updated)


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Missions"])
async def delete_mission(
    mission_id: UUID,
    current_user: TokenData = Depends(require_commander),
    db: AsyncSession = Depends(get_db),
):
    mission = await crud.get_mission(db, str(mission_id))
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    await crud.delete_mission(db, str(mission_id))
    logger.info("mission_deleted", mission_id=str(mission_id), actor=current_user.sub)


@router.get("/{mission_id}/events", tags=["Missions"])
async def get_mission_events(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
    db: AsyncSession = Depends(get_db),
):
    events = await crud.get_mission_events(db, str(mission_id))
    return [{"id": e.id, "event_type": e.event_type, "actor": e.actor,
             "summary": e.summary, "timestamp": e.timestamp} for e in events]
