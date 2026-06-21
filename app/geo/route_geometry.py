"""
AXIOM Route Geometry Engine
Nexxon National | Unclassified

Builds route line geometry from waypoints.
Calculates total distance, segment distances,
and generates alternate route geometry from CoA data.
"""

import math
from app.models import Waypoint, CoA
from app.ai.threat_analyzer import haversine_distance


def route_to_geojson(
    waypoints: list[Waypoint],
    label: str = "Primary Route",
    color: str = "#00FF41",
    is_alternate: bool = False,
) -> dict:
    """
    Convert an ordered list of waypoints into a GeoJSON LineString
    with distance and timing metadata.
    """
    if len(waypoints) < 2:
        return {"type": "FeatureCollection", "features": []}

    sorted_wps = sorted(waypoints, key=lambda w: w.sequence)
    coordinates = [[wp.longitude, wp.latitude] for wp in sorted_wps]

    # Calculate segment distances
    total_distance_m = 0.0
    segments = []
    for i in range(len(sorted_wps) - 1):
        a, b = sorted_wps[i], sorted_wps[i + 1]
        dist = haversine_distance(a.latitude, a.longitude, b.latitude, b.longitude)
        total_distance_m += dist
        segments.append({
            "from": a.name,
            "to": b.name,
            "distance_m": round(dist, 1),
        })

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": coordinates,
                },
                "properties": {
                    "label": label,
                    "color": color,
                    "is_alternate": is_alternate,
                    "total_distance_m": round(total_distance_m, 1),
                    "total_distance_km": round(total_distance_m / 1000, 2),
                    "waypoint_count": len(sorted_wps),
                    "segments": segments,
                    "line_width": 2 if is_alternate else 3,
                    "line_dash": [4, 2] if is_alternate else [],
                },
            }
        ],
    }


def calculate_operational_distance(waypoints: list[Waypoint]) -> dict:
    """
    Returns full distance breakdown for mission planning.
    """
    if not waypoints:
        return {"total_m": 0, "total_km": 0, "segments": []}

    sorted_wps = sorted(waypoints, key=lambda w: w.sequence)
    total = 0.0
    segments = []

    for i in range(len(sorted_wps) - 1):
        a, b = sorted_wps[i], sorted_wps[i + 1]
        dist = haversine_distance(a.latitude, a.longitude, b.latitude, b.longitude)
        total += dist
        segments.append({
            "from": a.name,
            "to": b.name,
            "distance_m": round(dist, 1),
            "distance_km": round(dist / 1000, 2),
        })

    return {
        "total_m": round(total, 1),
        "total_km": round(total / 1000, 2),
        "segments": segments,
    }
