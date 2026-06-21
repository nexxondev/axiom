"""
AXIOM Wrist Adapter
Nexxon National | Unclassified

Wrist device display. 2 inch screen.
Operator glances for 1 second max.
Three fields only: status, threats, action.
Future: Apple Watch Ultra, Garmin Tactix.
"""

from app.adapters.base import (
    BaseDisplayAdapter, DisplayFormFactor, DisplayConstraints,
    MissionStateInput, AdapterResponse
)


class WristAdapter(BaseDisplayAdapter):
    form_factor = DisplayFormFactor.WRIST
    constraints = DisplayConstraints(
        form_factor=DisplayFormFactor.WRIST,
        screen_width_px=396,
        screen_height_px=484,
        is_night_vision_compatible=True,
        max_data_fields=3,
        supports_map=False,
        supports_touch=True,
        operator_in_motion=True,
        bandwidth_limited=True,
    )

    def render(self, state: MissionStateInput) -> AdapterResponse:
        alert = self._get_threat_alert(state)

        # Wrist shows exactly three things:
        # 1. Go / Hold / Abort
        # 2. Threat count
        # 3. Action required indicator
        go_status = self._get_go_status(state)

        primary_fields = {
            "go_status": go_status,
            "threats": state.active_threat_count,
            "action": "YES" if state.commander_action_required else "NO",
        }

        alerts = [alert] if alert else []

        return AdapterResponse(
            form_factor=self.form_factor,
            primary_fields=primary_fields,
            alerts=alerts,
            map_config=None,
            action_buttons=[
                {"id": "ack", "label": "ACK", "style": "primary"},
            ],
            refresh_interval_ms=2000,
            payload_size="micro",
        )

    def _get_go_status(self, state: MissionStateInput) -> str:
        if state.mission_status == "aborted":
            return "ABORT"
        if state.commander_action_required:
            return "HOLD"
        if state.active_threat_count > 2:
            return "CAUTION"
        if state.mission_status == "active":
            return "GO"
        return state.mission_status.upper()
