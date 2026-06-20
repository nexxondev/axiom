"""
AXIOM CoA Generator
Nexxon National | Unclassified

Calls the AI reasoning engine to generate
Courses of Action when a replan is triggered.
Supports cloud (OpenAI) and local model modes.
"""

import json
import os
from app.ai.prompts import SYSTEM_PROMPT, REPLAN_PROMPT, THREAT_ANALYSIS_PROMPT
from app.models import Mission, Waypoint, Threat, Asset
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger("axiom.coa_generator")


def _format_waypoints(waypoints: list[Waypoint]) -> str:
    if not waypoints:
        return "No waypoints defined"
    sorted_wps = sorted(waypoints, key=lambda w: w.sequence)
    lines = []
    for wp in sorted_wps:
        alt = f" ALT:{wp.altitude_m}m" if wp.altitude_m else ""
        lines.append(
            f"  [{wp.sequence}] {wp.name} ({wp.waypoint_type}) "
            f"@ {wp.latitude:.4f},{wp.longitude:.4f}{alt}"
        )
    return "\n".join(lines)


def _format_threats(threats: list[Threat]) -> str:
    if not threats:
        return "No active threats"
    lines = []
    for t in threats:
        lines.append(
            f"  - {t.threat_type} | Level:{t.threat_level} | "
            f"Confidence:{t.confidence:.0%} | "
            f"Pos:{t.latitude:.4f},{t.longitude:.4f} | "
            f"Radius:{t.radius_m}m | Source:{t.source or 'UNKNOWN'}"
        )
    return "\n".join(lines)


def _format_assets(assets: list[Asset]) -> str:
    if not assets:
        return "No assets assigned"
    return "\n".join(
        f"  - {a.callsign} ({a.asset_type}) Status:{a.status}"
        for a in assets
    )


async def generate_coas(
    mission: Mission,
    waypoints: list[Waypoint],
    threats: list[Threat],
    assets: list[Asset],
    num_coas: int = 3,
) -> dict:
    """
    Generate Courses of Action for a mission replan.
    Returns structured CoA data from the AI engine.
    """
    prompt = REPLAN_PROMPT.format(
        mission_name=mission.name,
        mission_type=mission.mission_type,
        mission_status=mission.status,
        waypoints=_format_waypoints(waypoints),
        threats=_format_threats(threats),
        assets=_format_assets(assets),
        num_coas=num_coas,
    )

    logger.info("coa_generation_start", mission_id=str(mission.id), num_coas=num_coas)

    # Check if we have an API key for cloud mode
    api_key = os.environ.get("OPENAI_API_KEY", "")
    
    if not api_key or api_key == "your_key_here":
        logger.info("coa_generation_mode", mode="simulation")
        return _simulated_coas(mission, threats)

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(
            model=settings.AI_MODEL,
            temperature=0.3,  # Low temp = consistent tactical reasoning
            api_key=api_key,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]

        response = await llm.ainvoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if model adds them anyway
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]

        result = json.loads(raw)
        logger.info("coa_generation_complete", mode="ai", num_coas=len(result.get("coas", [])))
        return result

    except Exception as e:
        logger.error("coa_generation_error", error=str(e))
        return _simulated_coas(mission, threats)


def _simulated_coas(mission: Mission, threats: list[Threat]) -> dict:
    """
    High-fidelity simulation mode for demo/testing without an API key.
    Returns realistic CoA data that demonstrates full platform capability.
    """
    threat_summary = "Unknown threat"
    if threats:
        t = threats[0]
        threat_summary = (
            f"{t.threat_type} detected at {t.latitude:.4f},{t.longitude:.4f} "
            f"with {t.confidence:.0%} confidence, {t.radius_m}m threat radius"
        )

    return {
        "replan_triggered": True,
        "threat_summary": threat_summary,
        "coas": [
            {
                "title": "CoA 1 — Northern Bypass",
                "risk_level": "MEDIUM",
                "summary": (
                    f"Reroute {mission.name} north of the threat axis, "
                    "adding approximately 4km to the approach. "
                    "Maintains primary objective while avoiding threat radius."
                ),
                "waypoint_changes": [
                    "Insert WP-NORTH-1 at threat+2km north",
                    "Insert WP-NORTH-2 rejoining original route past threat",
                    "Objective and egress unchanged"
                ],
                "time_delta_minutes": 12,
                "reasoning": (
                    "Northern terrain provides concealment. "
                    "Threat confidence is high enough to warrant route change. "
                    "Time delta acceptable within mission window."
                )
            },
            {
                "title": "CoA 2 — Suppress and Advance",
                "risk_level": "HIGH",
                "summary": (
                    "Engage threat with ISR asset to fix in place, "
                    "then advance on original route under suppression. "
                    "Maintains original timeline but increases contact probability."
                ),
                "waypoint_changes": [
                    "No route change",
                    "ISR asset redirected to threat position",
                    "Ground element holds at ORP until threat suppressed"
                ],
                "time_delta_minutes": 8,
                "reasoning": (
                    "Fastest option if ISR asset is available and threat "
                    "can be fixed before ground element advance. "
                    "High risk if suppression is incomplete."
                )
            },
            {
                "title": "CoA 3 — Hold and Reassess",
                "risk_level": "LOW",
                "summary": (
                    "Hold at current ORP, gather additional ISR on threat, "
                    "and reassess within 30 minutes. "
                    "Lowest risk but may compromise mission timing."
                ),
                "waypoint_changes": [
                    "All elements hold at current positions",
                    "ISR asset redirected for threat characterization",
                    "Mission window reassessed at T+30"
                ],
                "time_delta_minutes": 30,
                "reasoning": (
                    "Threat confidence is based on single source. "
                    "Additional ISR may clarify threat nature and allow "
                    "more precise CoA selection."
                )
            }
        ],
        "recommended_coa": "CoA 1 — Northern Bypass",
        "commander_decision_required": True
    }
