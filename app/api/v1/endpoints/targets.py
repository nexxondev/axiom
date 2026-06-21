"""
AXIOM Target Management API
Nexxon National | Unclassified

Full target lifecycle: nomination, prioritization,
ROE evaluation, designation, deconfliction.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime, timezone
from app.models.target import (
    Target, TargetCreate, TargetUpdate,
    TargetType, TargetStatus, ROEStatus,
)
from app.models import Asset, Waypoint, AssetType, AssetStatus, WaypointType
from app.services.target_manager import prioritize_targets, deconflict_targets, evaluate_roe
from app.api.deps import require_staff, require_commander, require_observer
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("axiom.targets")

# In-memory store for M05 — DB in M08
_targets: dict[str, Target] = {}


def _demo_assets(mission_id: UUID) -> list[Asset]:
    return [
        Asset(callsign="GHOST-1", asset_type=AssetType.GROUND_ELEMENT,
              status=AssetStatus.MOVING, latitude=34.5110, longitude=69.1510,
              mission_id=mission_id),
        Asset(callsign="RAVEN-2", asset_type=AssetType.ISR_DRONE,
              status=AssetStatus.ON_STATION, latitude=34.5200, longitude=69.1700,
              mission_id=mission_id),
    ]


def _demo_waypoints(mission_id: UUID) -> list[Waypoint]:
    return [
        Waypoint(name="SP-ALPHA", waypoint_type=WaypointType.SP,
                 latitude=34.5100, longitude=69.1500, sequence=0, mission_id=mission_id),
        Waypoint(name="OBJ-FALCON", waypoint_type=WaypointType.OBJ,
                 latitude=34.5260, longitude=69.1703, sequence=1, mission_id=mission_id),
    ]


@router.get("/", tags=["Targets"])
async def list_targets(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
) -> list[Target]:
    """List all targets for a mission."""
    return [t for t in _targets.values() if t.mission_id == mission_id]


@router.post("/", status_code=status.HTTP_201_CREATED, tags=["Targets"])
async def nominate_target(
    payload: TargetCreate,
    current_user: TokenData = Depends(require_staff),
) -> Target:
    """
    Nominate a new target.
    Automatically evaluates initial ROE compliance.
    Requires Staff or above.
    """
    target = Target(**payload.model_dump())

    # Immediate ROE evaluation on nomination
    assets = _demo_assets(payload.mission_id)
    roe_status, roe_reason = evaluate_roe(target, assets)
    target.roe_status = roe_status

    _targets[str(target.id)] = target

    logger.info(
        "target_nominated",
        target_id=str(target.id),
        name=target.name,
        roe_status=roe_status,
        actor=current_user.sub,
    )
    return target


@router.get("/prioritize", tags=["Targets"])
async def get_prioritized_targets(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
) -> dict:
    """
    Return all targets ranked by tactical priority with ROE status.
    The core target management output — what commanders see.
    """
    mission_targets = [t for t in _targets.values() if t.mission_id == mission_id]

    if not mission_targets:
        # Return demo targets if none exist
        mission_targets = _demo_target_list(mission_id)

    waypoints = _demo_waypoints(mission_id)
    assets = _demo_assets(mission_id)

    ranked = prioritize_targets(mission_targets, waypoints, assets)
    conflicts = deconflict_targets(mission_targets)

    engageable = [t for t in ranked if t["engageable"]]
    restricted = [t for t in ranked if not t["engageable"]]

    return {
        "mission_id": str(mission_id),
        "total_targets": len(ranked),
        "engageable_count": len(engageable),
        "restricted_count": len(restricted),
        "targets": ranked,
        "deconfliction_alerts": conflicts,
        "commander_decision_required": len(engageable) > 0,
    }


@router.patch("/{target_id}", tags=["Targets"])
async def update_target(
    target_id: UUID,
    payload: TargetUpdate,
    current_user: TokenData = Depends(require_staff),
) -> Target:
    """Update target status or priority. Requires Staff or above."""
    target = _targets.get(str(target_id))
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    update_data = payload.model_dump(exclude_unset=True)
    updated = target.model_copy(update={
        **update_data,
        "updated_at": datetime.now(timezone.utc)
    })
    _targets[str(target_id)] = updated
    return updated


@router.post("/{target_id}/designate", tags=["Targets"])
async def designate_target(
    target_id: UUID,
    asset_callsign: str,
    current_user: TokenData = Depends(require_commander),
) -> dict:
    """
    Designate a target for engagement by a specific asset.
    Commander only. ROE must be COMPLIANT.
    """
    target = _targets.get(str(target_id))
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    if target.roe_status == ROEStatus.PROHIBITED:
        raise HTTPException(
            status_code=403,
            detail="Target is PROHIBITED under current ROE. Designation denied.",
        )

    if target.roe_status in [ROEStatus.RESTRICTED, ROEStatus.HOLD]:
        raise HTTPException(
            status_code=403,
            detail=f"Target ROE status is {target.roe_status}. Commander must clear before designation.",
        )

    updated = target.model_copy(update={
        "status": TargetStatus.DESIGNATED,
        "designated_asset": asset_callsign,
        "engagement_authority": current_user.sub,
        "updated_at": datetime.now(timezone.utc),
    })
    _targets[str(target_id)] = updated

    logger.info(
        "target_designated",
        target_id=str(target_id),
        asset=asset_callsign,
        authority=current_user.sub,
    )

    return {
        "target_id": str(target_id),
        "name": target.name,
        "status": "designated",
        "designated_asset": asset_callsign,
        "engagement_authority": current_user.sub,
        "roe_status": target.roe_status,
        "message": f"Target {target.name} designated to {asset_callsign}. Awaiting execution.",
    }


def _demo_target_list(mission_id: UUID) -> list[Target]:
    """Demo targets for Operation Nightfall."""
    return [
        Target(
            mission_id=mission_id,
            name="JACKPOT-1",
            target_type=TargetType.HVT,
            latitude=34.5265, longitude=69.1705,
            confidence=0.91,
            intelligence_source="SIGINT/ISR",
            description="Senior network facilitator, confirmed at objective",
        ),
        Target(
            mission_id=mission_id,
            name="JACKPOT-2",
            target_type=TargetType.HVI,
            latitude=34.5260, longitude=69.1700,
            confidence=0.74,
            intelligence_source="HUMINT",
            description="Associate, probable location",
        ),
        Target(
            mission_id=mission_id,
            name="VEHICLE-ALPHA",
            target_type=TargetType.VEHICLE,
            latitude=34.5195, longitude=69.1610,
            confidence=0.88,
            intelligence_source="ISR_DRONE_ALPHA",
            description="Armed technical, blocking route",
        ),
    ]
