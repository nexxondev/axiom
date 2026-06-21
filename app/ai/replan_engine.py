"""
AXIOM Replan Engine
Nexxon National | Unclassified

LangGraph stateful agent that orchestrates
the full replanning workflow:
1. Analyze incoming threat
2. Check route intersection
3. Generate CoAs
4. Package result for commander review

This is the core AI loop that makes AXIOM
different from every other tactical tool.
"""

from uuid import UUID
from datetime import datetime, timezone
from app.ai.threat_analyzer import threat_intersects_route
from app.ai.coa_generator import generate_coas
from app.models import (
    Mission, Waypoint, Threat, Asset,
    CoA, CoASource, CoAStatus,
    MissionEvent, EventType,
)
from app.core.logging import get_logger

logger = get_logger("axiom.replan_engine")


class ReplanResult:
    def __init__(
        self,
        triggered: bool,
        threat_summary: str,
        coas: list[CoA],
        recommended_coa: str,
        events: list[MissionEvent],
        processing_ms: float,
    ):
        self.triggered = triggered
        self.threat_summary = threat_summary
        self.coas = coas
        self.recommended_coa = recommended_coa
        self.events = events
        self.processing_ms = processing_ms

    def to_dict(self) -> dict:
        return {
            "replan_triggered": self.triggered,
            "threat_summary": self.threat_summary,
            "coas": [
                {
                    "id": str(coa.id),
                    "title": coa.title,
                    "risk_level": coa.risk_level,
                    "summary": coa.summary,
                    "reasoning": coa.reasoning,
                    "estimated_duration_min": coa.estimated_duration_min,
                    "waypoints": coa.waypoints,
                    "status": coa.status,
                    "source": coa.source,
                }
                for coa in self.coas
            ],
            "recommended_coa": self.recommended_coa,
            "commander_decision_required": True,
            "processing_ms": round(self.processing_ms, 1),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


async def run_replan(
    mission: Mission,
    waypoints: list[Waypoint],
    threats: list[Threat],
    assets: list[Asset],
) -> ReplanResult:
    """
    Main replan orchestration loop.
    Called when a new threat is added or route conditions change.
    """
    import time
    start = time.perf_counter()
    events: list[MissionEvent] = []

    logger.info("replan_start", mission_id=str(mission.id), threat_count=len(threats))

    # Log replan trigger event
    events.append(MissionEvent(
        mission_id=mission.id,
        event_type=EventType.REPLAN_TRIGGERED,
        actor="AXIOM",
        summary=f"Replan triggered for {mission.name} — {len(threats)} active threat(s)",
        payload={"threat_count": len(threats)},
    ))

    # Step 1: Check if any threat actually intersects the route
    active_threats = [t for t in threats if t.is_active]
    route_threatened = False
    threatening_threats = []

    for threat in active_threats:
        intersects, distance_m, nearest_wp = threat_intersects_route(threat, waypoints)
        if intersects:
            route_threatened = True
            threatening_threats.append(threat)
            logger.info(
                "route_threat_confirmed",
                threat_type=threat.threat_type,
                distance_m=round(distance_m, 1),
                nearest_wp=nearest_wp,
            )

    if not route_threatened:
        elapsed = (time.perf_counter() - start) * 1000
        logger.info("replan_no_action_required", mission_id=str(mission.id))
        events.append(MissionEvent(
            mission_id=mission.id,
            event_type=EventType.REPLAN_COMPLETE,
            actor="AXIOM",
            summary="Threat analysis complete — no route intersection detected",
            payload={"action": "none_required"},
        ))
        return ReplanResult(
            triggered=False,
            threat_summary="No threats intersect current route",
            coas=[],
            recommended_coa="",
            events=events,
            processing_ms=elapsed,
        )

    # Step 2: Generate CoAs via AI engine
    ai_result = await generate_coas(
        mission=mission,
        waypoints=waypoints,
        threats=threatening_threats,
        assets=assets,
        num_coas=3,
    )

    # Step 3: Build CoA model objects
    coas: list[CoA] = []
    for coa_data in ai_result.get("coas", []):
        coa = CoA(
            mission_id=mission.id,
            title=coa_data["title"],
            source=CoASource.AI_GENERATED,
            summary=coa_data["summary"],
            risk_level=coa_data["risk_level"],
            estimated_duration_min=coa_data.get("time_delta_minutes"),
            waypoints=[{"change": c} for c in coa_data.get("waypoint_changes", [])],
            reasoning=coa_data.get("reasoning"),
            status=CoAStatus.GENERATED,
        )
        coas.append(coa)

    # Step 4: Log completion
    elapsed = (time.perf_counter() - start) * 1000
    events.append(MissionEvent(
        mission_id=mission.id,
        event_type=EventType.REPLAN_COMPLETE,
        actor="AXIOM",
        summary=f"Replan complete — {len(coas)} CoAs generated in {elapsed:.0f}ms",
        payload={
            "coa_count": len(coas),
            "recommended": ai_result.get("recommended_coa"),
            "processing_ms": elapsed,
        },
    ))

    logger.info(
        "replan_complete",
        mission_id=str(mission.id),
        coa_count=len(coas),
        processing_ms=round(elapsed, 1),
    )

    return ReplanResult(
        triggered=True,
        threat_summary=ai_result.get("threat_summary", ""),
        coas=coas,
        recommended_coa=ai_result.get("recommended_coa", ""),
        events=events,
        processing_ms=elapsed,
    )
