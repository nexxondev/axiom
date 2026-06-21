"""
AXIOM Display API
Nexxon National | Unclassified

Serves form-factor-optimized mission state.
Any device calls /display/{form_factor}/mission/{id}
and gets exactly what it needs — nothing more.
"""

from fastapi import APIRouter, Depends
from uuid import UUID
from app.adapters.base import DisplayFormFactor, MissionStateInput
from app.adapters.router import render_for_display
from app.api.deps import require_observer
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("axiom.display")


def _build_demo_state(mission_id: UUID) -> MissionStateInput:
    return MissionStateInput(
        mission_id=str(mission_id),
        mission_name="Operation Nightfall",
        mission_status="active",
        classification="UNCLASSIFIED",
        waypoint_count=4,
        active_threat_count=2,
        total_distance_km=3.7,
        current_phase="Infil",
        threats=[
            {"threat_type": "ENEMY_POSITION", "threat_level": "HIGH",
             "confidence": 0.87, "source": "ISR_DRONE_ALPHA"},
            {"threat_type": "IED", "threat_level": "MEDIUM",
             "confidence": 0.65, "source": "HUMINT"},
        ],
        targets=[
            {"name": "JACKPOT-1", "target_type": "HVT",
             "priority_score": 84.5, "engageable": True, "roe_status": "compliant"},
            {"name": "JACKPOT-2", "target_type": "HVI",
             "priority_score": 78.75, "engageable": True, "roe_status": "compliant"},
            {"name": "VEHICLE-ALPHA", "target_type": "VEHICLE",
             "priority_score": 77.75, "engageable": True, "roe_status": "compliant"},
            {"name": "LOW-CONF-TARGET", "target_type": "PERSONNEL",
             "priority_score": 61.5, "engageable": False, "roe_status": "restricted"},
        ],
        assets=[
            {"callsign": "GHOST-1", "asset_type": "GROUND_ELEMENT", "status": "moving"},
            {"callsign": "RAVEN-2", "asset_type": "ISR_DRONE", "status": "on_station"},
        ],
        commander_action_required=True,
        recommended_coa="CoA 1 — Northern Bypass",
    )


@router.get("/{form_factor}/mission/{mission_id}", tags=["Display Adapters"])
async def get_display_payload(
    form_factor: DisplayFormFactor,
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """
    Get mission state optimized for a specific display form factor.
    TABLET: full picture. HUD: 6 fields max. WRIST: 3 fields only.
    """
    state = _build_demo_state(mission_id)
    response = render_for_display(state, form_factor)

    logger.info(
        "display_served",
        form_factor=form_factor,
        mission_id=str(mission_id),
        payload_size=response.payload_size,
        actor=current_user.sub,
    )

    return response


@router.get("/all/mission/{mission_id}", tags=["Display Adapters"])
async def get_all_display_payloads(
    mission_id: UUID,
    current_user: TokenData = Depends(require_observer),
):
    """
    Get mission state for ALL form factors simultaneously.
    Shows the adapter system in action — same state, three views.
    """
    state = _build_demo_state(mission_id)

    return {
        "mission_id": str(mission_id),
        "adapters": {
            ff.value: render_for_display(state, ff).model_dump()
            for ff in [
                DisplayFormFactor.TABLET,
                DisplayFormFactor.HUD,
                DisplayFormFactor.WRIST,
            ]
        },
        "demonstration": "Same mission state. Three form factors. Three payloads.",
    }
