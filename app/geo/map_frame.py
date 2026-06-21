"""
AXIOM Map Frame Calculator
Nexxon National | Unclassified

Calculates the optimal map bounding box and center
for a given set of mission entities.
Ensures all threats, waypoints, and assets are visible
on any display form factor.
"""

from app.models import Waypoint, Threat, Asset


def calculate_map_frame(
    waypoints: list[Waypoint],
    threats: list[Threat],
    assets: list[Asset],
    padding_factor: float = 0.15,
) -> dict:
    """
    Calculate bounding box and center point for all mission entities.
    padding_factor adds margin around the operational area.
    Returns data ready for MapLibre fitBounds().
    """
    lats, lons = [], []

    for wp in waypoints:
        lats.append(wp.latitude)
        lons.append(wp.longitude)

    for t in threats:
        if t.is_active:
            # Include threat radius in bounding box
            radius_deg = t.radius_m / 111320
            lats.extend([t.latitude + radius_deg, t.latitude - radius_deg])
            lons.extend([t.longitude + radius_deg, t.longitude - radius_deg])

    for a in assets:
        if a.latitude and a.longitude:
            lats.append(a.latitude)
            lons.append(a.longitude)

    if not lats or not lons:
        # Default to Kabul if no data (demo fallback)
        return {
            "center": [69.1703, 34.5260],
            "bounds": [[69.0, 34.4], [69.3, 34.7]],
            "zoom": 12,
        }

    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_padding = (max_lat - min_lat) * padding_factor or 0.01
    lon_padding = (max_lon - min_lon) * padding_factor or 0.01

    return {
        "center": [
            round((min_lon + max_lon) / 2, 6),
            round((min_lat + max_lat) / 2, 6),
        ],
        "bounds": [
            [round(min_lon - lon_padding, 6), round(min_lat - lat_padding, 6)],
            [round(max_lon + lon_padding, 6), round(max_lat + lat_padding, 6)],
        ],
        "zoom": _estimate_zoom(max_lat - min_lat, max_lon - min_lon),
    }


def _estimate_zoom(lat_span: float, lon_span: float) -> int:
    """Estimate appropriate zoom level from coordinate span."""
    span = max(lat_span, lon_span)
    if span > 10: return 6
    if span > 5: return 7
    if span > 2: return 9
    if span > 1: return 10
    if span > 0.5: return 11
    if span > 0.1: return 13
    if span > 0.05: return 14
    return 15
