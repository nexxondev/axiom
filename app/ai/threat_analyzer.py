"""
AXIOM Threat Analyzer
Nexxon National | Unclassified

Determines whether an active threat intersects
the mission route and requires replanning.
Uses geometry first (fast, no AI cost), then
calls AI for tactical assessment if needed.
"""

import math
from app.models import Threat, Waypoint
from app.core.logging import get_logger

logger = get_logger("axiom.threat_analyzer")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance in meters between two lat/lon points.
    Used to determine if a threat radius intersects a waypoint or route segment.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def point_to_segment_distance(
    px: float, py: float,
    ax: float, ay: float,
    bx: float, by: float
) -> float:
    """
    Minimum distance from point P to line segment AB.
    Used to check if a threat intersects a route segment.
    Operates in approximate flat-earth lat/lon for short distances.
    """
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.sqrt((px - ax)**2 + (py - ay)**2)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx**2 + dy**2)))
    nearest_x, nearest_y = ax + t * dx, ay + t * dy
    return math.sqrt((px - nearest_x)**2 + (py - nearest_y)**2)


def threat_intersects_route(threat: Threat, waypoints: list[Waypoint]) -> tuple[bool, float, str]:
    """
    Returns (intersects, min_distance_m, nearest_waypoint_name).
    A threat intersects the route if its radius overlaps any route segment.
    """
    if not waypoints:
        return False, float("inf"), "NONE"

    sorted_wps = sorted(waypoints, key=lambda w: w.sequence)
    min_dist = float("inf")
    nearest_wp = sorted_wps[0].name

    # Check distance from threat to each waypoint
    for wp in sorted_wps:
        dist = haversine_distance(threat.latitude, threat.longitude, wp.latitude, wp.longitude)
        if dist < min_dist:
            min_dist = dist
            nearest_wp = wp.name

    # Check distance from threat to each route segment
    for i in range(len(sorted_wps) - 1):
        a, b = sorted_wps[i], sorted_wps[i + 1]
        seg_dist_deg = point_to_segment_distance(
            threat.latitude, threat.longitude,
            a.latitude, a.longitude,
            b.latitude, b.longitude
        )
        # Convert approximate degrees to meters (1 deg lat ~ 111km)
        seg_dist_m = seg_dist_deg * 111000
        if seg_dist_m < min_dist:
            min_dist = seg_dist_m
            nearest_wp = f"{a.name}→{b.name}"

    intersects = min_dist <= (threat.radius_m * threat.confidence)

    logger.info(
        "threat_route_analysis",
        threat_type=threat.threat_type,
        min_distance_m=round(min_dist, 1),
        threat_radius_m=threat.radius_m,
        intersects=intersects,
    )

    return intersects, min_dist, nearest_wp
