"""
AXIOM Display Adapter Base
Nexxon National | Unclassified

The contract that every display adapter must fulfill.
One mission state. Many form factors.
"""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class DisplayFormFactor(str, Enum):
    TABLET = "tablet"
    HUD = "hud"
    WRIST = "wrist"
    DESKTOP = "desktop"
    API = "api"


class DisplayConstraints(BaseModel):
    """Physical and contextual constraints of the display device."""
    form_factor: DisplayFormFactor
    screen_width_px: Optional[int] = None
    screen_height_px: Optional[int] = None
    is_night_vision_compatible: bool = False
    max_data_fields: int = 20
    supports_map: bool = True
    supports_touch: bool = True
    bandwidth_limited: bool = False
    operator_in_motion: bool = False


class MissionStateInput(BaseModel):
    """
    Full mission state — the single source of truth
    that all adapters receive and render differently.
    """
    mission_id: str
    mission_name: str
    mission_status: str
    classification: str
    waypoint_count: int
    active_threat_count: int
    total_distance_km: float
    current_phase: Optional[str] = None
    threats: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    last_replan_ms: Optional[float] = None
    recommended_coa: Optional[str] = None
    commander_action_required: bool = False


class AdapterResponse(BaseModel):
    """Structured display payload for a specific form factor."""
    form_factor: DisplayFormFactor
    primary_fields: dict[str, Any]
    alerts: list[str] = []
    map_config: Optional[dict[str, Any]] = None
    action_buttons: list[dict[str, str]] = []
    refresh_interval_ms: int = 5000
    payload_size: str = "full"


class BaseDisplayAdapter(ABC):
    """
    Abstract base for all display adapters.
    Subclasses implement render() for their form factor.
    """
    form_factor: DisplayFormFactor
    constraints: DisplayConstraints

    @abstractmethod
    def render(self, state: MissionStateInput) -> AdapterResponse:
        """Transform full mission state into form-factor-specific payload."""
        pass

    def _get_threat_alert(self, state: MissionStateInput) -> Optional[str]:
        if state.active_threat_count == 0:
            return None
        high = [t for t in state.threats
                if t.get("threat_level") in ["HIGH", "CRITICAL"]]
        if high:
            return f"THREAT: {high[0].get('threat_type','UNKNOWN')} {high[0].get('threat_level')}"
        return f"{state.active_threat_count} ACTIVE THREAT(S)"

    def _get_top_target(self, state: MissionStateInput) -> Optional[str]:
        engageable = [t for t in state.targets if t.get("engageable")]
        if engageable:
            return engageable[0].get("name", "UNKNOWN")
        return None
