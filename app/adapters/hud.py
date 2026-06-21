"""
AXIOM HUD Adapter
Nexxon National | Unclassified

Heads-up display overlay. Minimal data.
Operator is in motion — every field must be
readable in under 2 seconds.
Max 6 data fields. High contrast only.
"""

from app.adapters.base import (
    BaseDisplayAdapter, DisplayFormFactor, DisplayConstraints,
    MissionStateInput, AdapterResponse
)


class HUDAdapter(BaseDisplayAdapter):
    form_factor = DisplayFormFactor.HUD
    constraints = DisplayConstraints(
        form_factor=DisplayFormFactor.HUD,
        screen_width_px=1280,
        screen_height_px=720,
        is_night_vision_compatible=True,
        max_data_fields=6,
        supports_map=True,
        supports_touch=False,
        operator_in_motion=True,
        bandwidth_limited=False,
    )

    def render(self, state: MissionStateInput) -> AdapterResponse:
        alert = self._get_threat_alert(state)
        top_target = self._get_top_target(state)

        # HUD is ruthlessly minimal — only what matters RIGHT NOW
        primary_fields = {
            "op": state.mission_name,
            "status": state.mission_status.upper(),
            "threats": state.active_threat_count,
            "distance_km": state.total_distance_km,
            "action_required": state.commander_action_required,
        }

        if top_target:
            primary_fields["priority_target"] = top_target

        if state.recommended_coa:
            primary_fields["recommended_coa"] = state.recommended_coa[:40]

        alerts = []
        if alert:
            alerts.append(alert)
        if state.commander_action_required:
            alerts.append("COMMANDER ACTION REQUIRED")

        return AdapterResponse(
            form_factor=self.form_factor,
            primary_fields=primary_fields,
            alerts=alerts,
            map_config={
                "enabled": True,
                "zoom": 15,
                "show_threats": True,
                "show_route": True,
                "show_assets": False,
                "show_targets": False,
                "night_mode": True,
                "overlay_only": True,
            },
            action_buttons=[
                {"id": "replan", "label": "REPLAN", "style": "warning"},
                {"id": "abort", "label": "ABORT", "style": "danger"},
            ],
            refresh_interval_ms=1000,
            payload_size="minimal",
        )
