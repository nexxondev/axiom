"""
AXIOM Geospatial API
Nexxon National | Unclassified

Serves mission map data as GeoJSON.
The display layer (tablet, HUD, wrist) calls these
endpoints to render the tactical picture.
"""

from fastapi import APIRouter, Depends
from uuid import UUID
from app.geo.geojson_builder import waypoints_to_geojson, threats_to_geojson, assets_to_geojson
from app.geo.route_geometry import route_to_geojson, calculate_operational_distance
from app.geo.map_frame import calculate_map_frame
from app.models import (
    Mission, Waypoint, Threat, Asset,
    MissionType, MissionStatus, ClassificationLevel,
    WaypointType, ThreatType, ThreatLevel,
    AssetType, AssetStatus,
)
from app.api.deps import require_observer
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("axiom.geo")


def _demo_scenario(mission_id: UUID):
    """Standard demo scenario — Operation Nightfall."""
    mission = Mission(
        id=mission_id,
        name="Operation Nightfall",
        mission_type=MissionType.DA,
        status=MissionStatus.ACTIVE,
        classification=ClassificationLevel.UNCLASSIFIED,
    )
    waypoints = [
        Waypoint(name="SP-ALPHA", waypoint_type=WaypointType.SP,
                 latitude=34.5100, longitude=69.1500, sequence=0, mission_id=mission_id),
        Waypoint(name="ORP-BRAVO", waypoint_type=WaypointType.ORP,
                 latitude=34.5180, longitude=69.1580, sequence=1, mission_id=mission_id),
        Waypoint(name="OBJ-FALCON", waypoint_type=WaypointType.OBJ,
                 latitude=34.5260, longitude=69.1703, sequence=2, mission_id=mission_id),
        Waypoint(name="PZ-CHARLIE", waypoint_type=WaypointType.PZ,
                 latitude=34.5320, longitude=69.1800, sequence=3, mission_id=mission_id),
    ]
    threats = [
        Threat(threat_type=ThreatType.ENEMY_POSITION, threat_level=ThreatLevel.HIGH,
               latitude=34.5190, longitude=69.1600, radius_m=300.0, confidence=0.87,
               source="ISR_DRONE_ALPHA", mission_id=mission_id),
        Threat(threat_type=ThreatType.IED, threat_level=ThreatLevel.MEDIUM,
               latitude=34.5230, longitude=69.1650, radius_m=150.0, confidence=0.65,
               source="HUMINT", mission_id=mission_id),
    ]
    assets = [
        Asset(callsign="GHOST-1", asset_type=AssetType.GROUND_ELEMENT,
              status=AssetStatus.MOVING, latitude=34.5110, longitude=69.1510,
              mission_id=mission_id),
        Asset(callsign="RAVEN-2", asset_type=AssetType.ISR_DRONE,
              status=AssetStatus.ON_STATION, latitude=34.5200, longitude=69.1700,
              mission_id=mission_id),
    ]
    return mission, waypoints, threats, assets


@router.get("/mission/{mission_id}/map", tags=["Geospatial"])
async def get_mission_map(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """
    Full mission map package.
    Returns all GeoJSON layers + map frame for the display layer.
    Single call loads the complete tactical picture.
    """
    mission, waypoints, threats, assets = _demo_scenario(mission_id)

    route_geojson = route_to_geojson(waypoints, label="Primary Route")
    waypoint_geojson = waypoints_to_geojson(waypoints)
    threat_geojson = threats_to_geojson(threats)
    asset_geojson = assets_to_geojson(assets)
    map_frame = calculate_map_frame(waypoints, threats, assets)
    distances = calculate_operational_distance(waypoints)

    logger.info("map_data_served", mission_id=str(mission_id), actor=current_user.sub)

    return {
        "mission_id": str(mission_id),
        "mission_name": mission.name,
        "classification": mission.classification,
        "layers": {
            "route": route_geojson,
            "waypoints": waypoint_geojson,
            "threats": threat_geojson,
            "assets": asset_geojson,
        },
        "map_frame": map_frame,
        "operational_distance": distances,
        "layer_count": 4,
        "threat_count": len([t for t in threats if t.is_active]),
        "waypoint_count": len(waypoints),
    }


@router.get("/mission/{mission_id}/threats/geojson", tags=["Geospatial"])
async def get_threat_overlay(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """Threat overlay only — for incremental map updates."""
    _, _, threats, _ = _demo_scenario(mission_id)
    return threats_to_geojson(threats)


@router.get("/mission/{mission_id}/route/geojson", tags=["Geospatial"])
async def get_route_geojson(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """Route geometry only — for incremental map updates."""
    _, waypoints, _, _ = _demo_scenario(mission_id)
    return route_to_geojson(waypoints)


@router.get("/mission/{mission_id}/distance", tags=["Geospatial"])
async def get_operational_distance(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """Operational distance breakdown by route segment."""
    _, waypoints, _, _ = _demo_scenario(mission_id)
    return calculate_operational_distance(waypoints)
