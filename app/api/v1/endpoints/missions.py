"""
AXIOM Missions API
Nexxon National | Unclassified

Core mission CRUD. The entry point for all
operational data flowing into AXIOM.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.models import (
    Mission, MissionCreate, MissionUpdate,
    MissionStatus, EventType, ClassificationLevel,
)
from app.models.event import MissionEvent
from app.api.deps import require_staff, require_operator, require_observer, require_commander
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("missions")

# In-memory store for M02 — replaced with DB in M03
_missions: dict[str, Mission] = {}
_events: list[MissionEvent] = []


def _log_event(
    mission_id: UUID,
    event_type: EventType,
    actor: str,
    summary: str,
    payload: dict | None = None,
):
    event = MissionEvent(
        mission_id=mission_id,
        event_type=event_type,
        actor=actor,
        summary=summary,
        payload=payload,
    )
    _events.append(event)
    logger.info("mission_event", event_type=event_type, mission_id=str(mission_id))
    return event


@router.get("/", tags=["Missions"])
async def list_missions(
    current_user: TokenData = Depends(require_observer),
) -> list[Mission]:
    """List all missions visible to the current user."""
    missions = list(_missions.values())
    if current_user.role == "operator" and current_user.mission_ids:
        missions = [m for m in missions if str(m.id) in current_user.mission_ids]
    return missions


@router.post("/", status_code=status.HTTP_201_CREATED, tags=["Missions"])
async def create_mission(
    payload: MissionCreate,
    current_user: TokenData = Depends(require_staff),
) -> Mission:
    """Create a new mission. Requires Staff or above."""
    mission = Mission(
        **payload.model_dump(),
        created_by=current_user.sub,
    )
    _missions[str(mission.id)] = mission
    _log_event(
        mission.id,
        EventType.MISSION_CREATED,
        actor=current_user.sub,
        summary=f"Mission '{mission.name}' created",
        payload={"mission_type": mission.mission_type},
    )
    logger.info("mission_created", mission_id=str(mission.id), name=mission.name)
    return mission


@router.get("/{mission_id}", tags=["Missions"])
async def get_mission(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
) -> Mission:
    """Get a single mission by ID."""
    mission = _missions.get(str(mission_id))
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    if current_user.role == "operator" and str(mission_id) not in current_user.mission_ids:
        raise HTTPException(status_code=403, detail="Access denied to this mission")
    return mission


@router.patch("/{mission_id}", tags=["Missions"])
async def update_mission(
    mission_id: UUID,
    payload: MissionUpdate,
    current_user: TokenData = Depends(require_staff),
) -> Mission:
    """Update mission fields. Requires Staff or above."""
    mission = _missions.get(str(mission_id))
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    update_data = payload.model_dump(exclude_unset=True)
    updated = mission.model_copy(update={
        **update_data,
        "updated_at": datetime.now(timezone.utc)
    })
    _missions[str(mission_id)] = updated

    if "status" in update_data:
        _log_event(
            mission_id,
            EventType.MISSION_STATUS_CHANGED,
            actor=current_user.sub,
            summary=f"Mission status changed to {update_data['status']}",
            payload={"new_status": update_data["status"]},
        )
    return updated


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Missions"])
async def delete_mission(
    mission_id: UUID,
    current_user: TokenData = Depends(require_commander),
):
    """Delete a mission. Commander only."""
    if str(mission_id) not in _missions:
        raise HTTPException(status_code=404, detail="Mission not found")
    del _missions[str(mission_id)]
    logger.info("mission_deleted", mission_id=str(mission_id), actor=current_user.sub)


@router.get("/{mission_id}/events", tags=["Missions"])
async def get_mission_events(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
) -> list[MissionEvent]:
    """Get the full audit event log for a mission."""
    return [e for e in _events if e.mission_id == mission_id]
