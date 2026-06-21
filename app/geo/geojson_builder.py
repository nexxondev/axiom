"""
AXIOM GeoJSON Builder
Nexxon National | Unclassified

Converts AXIOM mission entities into GeoJSON —
the universal format for tactical map rendering.
Works with MapLibre GL, ATAK, and any GIS system.
"""

from app.models import Mission, Waypoint, Threat, Asset, Operator, CoA
from app.models.enums import ThreatLevel


# Color scheme — tactical, high contrast for HUD/tablet
THREAT_COLORS = {
    ThreatLevel.LOW: "#FFD700",       # Yellow
    ThreatLevel.MEDIUM: "#FF8C00",    # Orange
    ThreatLevel.HIGH: "#FF3B30",      # Red
    ThreatLevel.CRITICAL: "#8B0000",  # Dark red
}

WAYPOINT_COLORS = {
    "start_point": "#00FF41",         # Matrix green
    "objective": "#FF3B30",           # Red — the target
    "helicopter_landing_zone": "#00BFFF",
    "pickup_zone": "#00BFFF",
    "egress": "#FFD700",
    "casualty_collection_point": "#FF69B4",
    "default": "#FFFFFF",
}


def waypoints_to_geojson(waypoints: list[Waypoint]) -> dict:
    """Convert waypoints to a GeoJSON FeatureCollection."""
    features = []
    sorted_wps = sorted(waypoints, key=lambda w: w.sequence)

    for wp in sorted_wps:
        color = WAYPOINT_COLORS.get(wp.waypoint_type, WAYPOINT_COLORS["default"])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [wp.longitude, wp.latitude],
            },
            "properties": {
                "id": str(wp.id),
                "name": wp.name,
                "type": wp.waypoint_type,
                "sequence": wp.sequence,
                "altitude_m": wp.altitude_m,
                "is_alternate": wp.is_alternate,
                "notes": wp.notes,
                "color": color,
                "icon": _waypoint_icon(wp.waypoint_type),
            },
        })

    return {"type": "FeatureCollection", "features": features}


def threats_to_geojson(threats: list[Threat]) -> dict:
    """
    Convert threats to GeoJSON.
    Each threat produces TWO features:
    1. A point at the threat center
    2. A circle polygon representing the threat radius
    """
    features = []

    for threat in threats:
        if not threat.is_active:
            continue

        color = THREAT_COLORS.get(threat.threat_level, "#FF3B30")

        # Threat center point
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [threat.longitude, threat.latitude],
            },
            "properties": {
                "id": str(threat.id),
                "feature_type": "threat_center",
                "threat_type": threat.threat_type,
                "threat_level": threat.threat_level,
                "confidence": threat.confidence,
                "radius_m": threat.radius_m,
                "source": threat.source,
                "color": color,
                "is_active": threat.is_active,
            },
        })

        # Threat radius circle (approximated as polygon)
        circle_coords = _circle_polygon(
            threat.latitude, threat.longitude, threat.radius_m
        )
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [circle_coords],
            },
            "properties": {
                "id": str(threat.id),
                "feature_type": "threat_radius",
                "threat_type": threat.threat_type,
                "threat_level": threat.threat_level,
                "confidence": threat.confidence,
                "color": color,
                "fill_opacity": 0.25 * threat.confidence,
            },
        })

    return {"type": "FeatureCollection", "features": features}


def assets_to_geojson(assets: list[Asset]) -> dict:
    """Convert friendly assets to GeoJSON points."""
    features = []

    for asset in assets:
        if asset.latitude is None or asset.longitude is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [asset.longitude, asset.latitude],
            },
            "properties": {
                "id": str(asset.id),
                "callsign": asset.callsign,
                "asset_type": asset.asset_type,
                "status": asset.status,
                "color": "#00FF41",
                "icon": "friendly",
            },
        })

    return {"type": "FeatureCollection", "features": features}


def _waypoint_icon(waypoint_type: str) -> str:
    icons = {
        "start_point": "arrow-right",
        "objective": "crosshair",
        "helicopter_landing_zone": "helicopter",
        "pickup_zone": "helicopter",
        "drop_zone": "parachute",
        "casualty_collection_point": "hospital",
        "egress": "arrow-left",
        "objective_rally_point": "users",
    }
    return icons.get(waypoint_type, "map-pin")


def _circle_polygon(lat: float, lon: float, radius_m: float, steps: int = 64) -> list:
    """
    Approximate a circle as a GeoJSON polygon.
    radius_m in meters, returns list of [lon, lat] coordinate pairs.
    """
    import math
    coords = []
    for i in range(steps + 1):
        angle = math.radians(i * 360 / steps)
        # Convert radius from meters to approximate degrees
        dlat = (radius_m / 111320) * math.cos(angle)
        dlon = (radius_m / (111320 * math.cos(math.radians(lat)))) * math.sin(angle)
        coords.append([lon + dlon, lat + dlat])
    return coords
