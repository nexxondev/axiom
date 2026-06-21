"""
AXIOM Target Manager
Nexxon National | Unclassified

Priority scoring and ROE compliance engine.

PRIORITY SCORING FACTORS (weighted):
- Threat level to mission: 35%
- Intelligence confidence: 25%
- Proximity to friendly forces: 20%
- Target type / strategic value: 15%
- Time sensitivity: 5%

ROE GUARDRAILS are absolute. A target flagged
PROHIBITED cannot be engaged regardless of
priority score. This is non-negotiable.
"""

from app.models.target import Target, TargetType, TargetStatus, ROEStatus
from app.models import Waypoint, Asset
from app.ai.threat_analyzer import haversine_distance
from app.core.logging import get_logger

logger = get_logger("axiom.target_manager")


# Scoring weights — must sum to 1.0
WEIGHTS = {
    "threat_level": 0.35,
    "confidence": 0.25,
    "proximity_to_friendly": 0.20,
    "target_type": 0.15,
    "time_sensitivity": 0.05,
}

# Target type strategic value scores (0-100)
TARGET_TYPE_VALUE = {
    TargetType.HVT: 100,
    TargetType.HVI: 90,
    TargetType.INFRASTRUCTURE: 70,
    TargetType.VEHICLE: 60,
    TargetType.EQUIPMENT: 50,
    TargetType.PERSONNEL: 40,
    TargetType.MATERIAL: 30,
}

# ROE rules — conditions that trigger each status
ROE_RULES = {
    "civilian_proximity_m": 100,     # RESTRICTED if civilians within 100m
    "friendly_proximity_m": 200,     # HOLD if friendlies within 200m
    "min_confidence": 0.5,           # RESTRICTED if confidence below 50%
    "prohibited_types": [],          # Types that are always PROHIBITED (mission-specific)
}


def calculate_priority_score(
    target: Target,
    waypoints: list[Waypoint],
    assets: list[Asset],
    threat_level_score: float = 75.0,
    time_sensitivity: float = 50.0,
) -> float:
    """
    Calculate a 0-100 priority score for a target.
    Higher = higher priority for engagement.
    """
    scores = {}

    # 1. Threat level to mission (passed in from threat analysis)
    scores["threat_level"] = min(100.0, threat_level_score)

    # 2. Intelligence confidence
    scores["confidence"] = target.confidence * 100

    # 3. Proximity to friendly forces (inverse — closer = lower score)
    min_friendly_dist = float("inf")
    for asset in assets:
        if asset.latitude and asset.longitude:
            dist = haversine_distance(
                target.latitude, target.longitude,
                asset.latitude, asset.longitude
            )
            min_friendly_dist = min(min_friendly_dist, dist)

    if min_friendly_dist == float("inf"):
        scores["proximity_to_friendly"] = 50.0  # Unknown — neutral
    elif min_friendly_dist < 100:
        scores["proximity_to_friendly"] = 5.0   # Too close — high risk
    elif min_friendly_dist < 500:
        scores["proximity_to_friendly"] = 30.0
    elif min_friendly_dist < 1000:
        scores["proximity_to_friendly"] = 60.0
    else:
        scores["proximity_to_friendly"] = 90.0  # Safe distance

    # 4. Target type strategic value
    scores["target_type"] = TARGET_TYPE_VALUE.get(target.target_type, 50)

    # 5. Time sensitivity
    scores["time_sensitivity"] = time_sensitivity

    # Weighted sum
    final_score = sum(
        scores[factor] * weight
        for factor, weight in WEIGHTS.items()
    )

    logger.info(
        "target_scored",
        target_id=str(target.id),
        target_name=target.name,
        scores=scores,
        final_score=round(final_score, 2),
    )

    return round(final_score, 2)


def evaluate_roe(
    target: Target,
    assets: list[Asset],
    civilian_proximity_m: float = float("inf"),
) -> tuple[ROEStatus, str]:
    """
    Evaluate ROE compliance for a target.
    Returns (ROEStatus, reason_string).

    ROE evaluation is ALWAYS run before any engagement designation.
    PROHIBITED status cannot be overridden by any user or role.
    """
    # Hard stops first
    if target.target_type in ROE_RULES["prohibited_types"]:
        return ROEStatus.PROHIBITED, f"Target type {target.target_type} prohibited by current ROE"

    if target.confidence < ROE_RULES["min_confidence"]:
        return ROEStatus.RESTRICTED, (
            f"Intelligence confidence {target.confidence:.0%} below minimum "
            f"{ROE_RULES['min_confidence']:.0%} required for engagement"
        )

    # Civilian proximity
    if civilian_proximity_m < ROE_RULES["civilian_proximity_m"]:
        return ROEStatus.RESTRICTED, (
            f"Civilian presence detected within {civilian_proximity_m:.0f}m "
            f"(minimum safe distance: {ROE_RULES['civilian_proximity_m']}m)"
        )

    # Friendly fire check
    for asset in assets:
        if asset.latitude and asset.longitude:
            dist = haversine_distance(
                target.latitude, target.longitude,
                asset.latitude, asset.longitude
            )
            if dist < ROE_RULES["friendly_proximity_m"]:
                return ROEStatus.HOLD, (
                    f"Friendly element {asset.callsign} within "
                    f"{dist:.0f}m of target (minimum: {ROE_RULES['friendly_proximity_m']}m)"
                )

    return ROEStatus.COMPLIANT, "All ROE conditions met"


def prioritize_targets(
    targets: list[Target],
    waypoints: list[Waypoint],
    assets: list[Asset],
) -> list[dict]:
    """
    Score, evaluate ROE, and rank all targets.
    Returns sorted list with full tactical assessment.
    """
    results = []

    for target in targets:
        if target.status in [TargetStatus.NEUTRALIZED, TargetStatus.RELEASED]:
            continue

        # Score
        score = calculate_priority_score(target, waypoints, assets)

        # ROE evaluation
        roe_status, roe_reason = evaluate_roe(target, assets)

        # Apply priority override if set by commander
        effective_priority = target.priority_override * 10 if target.priority_override else score

        results.append({
            "target_id": str(target.id),
            "name": target.name,
            "target_type": target.target_type,
            "status": target.status,
            "latitude": target.latitude,
            "longitude": target.longitude,
            "confidence": target.confidence,
            "priority_score": score,
            "effective_priority": effective_priority,
            "roe_status": roe_status,
            "roe_reason": roe_reason,
            "engageable": roe_status == ROEStatus.COMPLIANT,
            "designated_asset": target.designated_asset,
        })

    # Sort by effective priority descending
    results.sort(key=lambda x: x["effective_priority"], reverse=True)

    # Add rank
    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results


def deconflict_targets(targets: list[Target], proximity_m: float = 50.0) -> list[dict]:
    """
    Identify targets that are too close together to engage independently.
    Returns list of deconfliction recommendations.
    """
    conflicts = []

    for i, t1 in enumerate(targets):
        for t2 in targets[i+1:]:
            dist = haversine_distance(
                t1.latitude, t1.longitude,
                t2.latitude, t2.longitude
            )
            if dist < proximity_m:
                conflicts.append({
                    "target_1": t1.name,
                    "target_2": t2.name,
                    "distance_m": round(dist, 1),
                    "recommendation": "Engage simultaneously or confirm deconfliction",
                })

    return conflicts
