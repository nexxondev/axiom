"""
AXIOM Replan API Endpoint
Nexxon National | Unclassified

The tactical AI interface. Commanders call this
when threats emerge or conditions change.
"""

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from pydantic import BaseModel
from app.ai.replan_engine import run_replan
from app.models import (
    Mission, Waypoint, Threat, Asset,
    MissionStatus, MissionType,
    WaypointType, ThreatType, ThreatLevel,
    AssetType, AssetStatus,
    ClassificationLevel,
)
from app.api.deps import require_operator
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("axiom.replan_api")


class ReplanRequest(BaseModel):
    mission_id: UUID
    notes: str | None = None


@router.post("/replan", tags=["AI Engine"])
async def trigger_replan(
    payload: ReplanRequest,
    current_user: TokenData = Depends(require_operator),
):
    """
    Trigger AI mission replanning.

    Analyzes active threats against the current route
    and generates Courses of Action for commander review.
    Requires Operator role or above.
    """
    logger.info(
        "replan_requested",
        mission_id=str(payload.mission_id),
        actor=current_user.sub,
    )

    # For M03 we build a rich demo scenario inline
    # M04 (Geospatial) will wire this to the live mission store
    mission = Mission(
        id=payload.mission_id,
        name="Operation Nightfall",
        mission_type=MissionType.DA,
        status=MissionStatus.ACTIVE,
        classification=ClassificationLevel.UNCLASSIFIED,
        description="Direct action on HVT, Kabul sector",
    )

    waypoints = [
        Waypoint(
            name="SP-ALPHA", waypoint_type=WaypointType.SP,
            latitude=34.5100, longitude=69.1500, sequence=0,
            mission_id=mission.id,
        ),
        Waypoint(
            name="ORP-BRAVO", waypoint_type=WaypointType.ORP,
            latitude=34.5180, longitude=69.1580, sequence=1,
            mission_id=mission.id,
        ),
        Waypoint(
            name="OBJ-FALCON", waypoint_type=WaypointType.OBJ,
            latitude=34.5260, longitude=69.1703, sequence=2,
            mission_id=mission.id,
        ),
        Waypoint(
            name="PZ-CHARLIE", waypoint_type=WaypointType.PZ,
            latitude=34.5320, longitude=69.1800, sequence=3,
            mission_id=mission.id,
        ),
    ]

    threats = [
        Threat(
            threat_type=ThreatType.ENEMY_POSITION,
            threat_level=ThreatLevel.HIGH,
            latitude=34.5190,
            longitude=69.1600,
            radius_m=300.0,
            confidence=0.87,
            source="ISR_DRONE_ALPHA",
            mission_id=mission.id,
        )
    ]

    assets = [
        Asset(
            callsign="GHOST-1",
            asset_type=AssetType.GROUND_ELEMENT,
            status=AssetStatus.MOVING,
            mission_id=mission.id,
        ),
        Asset(
            callsign="RAVEN-2",
            asset_type=AssetType.ISR_DRONE,
            status=AssetStatus.ON_STATION,
            mission_id=mission.id,
        ),
    ]

    result = await run_replan(
        mission=mission,
        waypoints=waypoints,
        threats=threats,
        assets=assets,
    )

    return result.to_dict()
