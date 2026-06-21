"""
AXIOM Tablet Adapter
Nexxon National | Unclassified

Full tactical picture for ruggedized tablet.
Panasonic Toughbook, Samsung Tab Active, Dell Latitude Rugged.
"""

from app.adapters.base import (
    BaseDisplayAdapter, DisplayFormFactor, DisplayConstraints,
    MissionStateInput, AdapterResponse
)


class TabletAdapter(BaseDisplayAdapter):
    form_factor = DisplayFormFactor.TABLET
    constraints = DisplayConstraints(
        form_factor=DisplayFormFactor.TABLET,
        screen_width_px=1920,
        screen_height_px=1200,
        max_data_fields=50,
        supports_map=True,
        supports_touch=True,
        operator_in_motion=False,
    )

    def render(self, state: MissionStateInput) -> AdapterResponse:
        alert = self._get_threat_alert(state)
        top_target = self._get_top_target(state)

        primary_fields = {
            "mission_name": state.mission_name,
            "mission_status": state.mission_status,
            "classification": state.classification,
            "waypoints": state.waypoint_count,
            "active_threats": state.active_threat_count,
            "distance_km": state.total_distance_km,
            "current_phase": state.current_phase,
            "top_target": top_target,
            "commander_action_required": state.commander_action_required,
            "recommended_coa": state.recommended_coa,
            "threats": state.threats,
            "targets": state.targets[:5],
            "assets": state.assets,
        }

        action_buttons = [
            {"id": "replan", "label": "TRIGGER AI REPLAN", "style": "warning"},
            {"id": "abort", "label": "ABORT MISSION", "style": "danger"},
            {"id": "casevac", "label": "REQUEST CASEVAC", "style": "info"},
        ]

        if state.commander_action_required:
            action_buttons.insert(0, {
                "id": "approve_coa",
                "label": "APPROVE COA",
                "style": "success"
            })

        return AdapterResponse(
            form_factor=self.form_factor,
            primary_fields=primary_fields,
            alerts=[alert] if alert else [],
            map_config={
                "enabled": True,
                "zoom": 14,
                "show_threats": True,
                "show_route": True,
                "show_assets": True,
                "show_targets": True,
                "night_mode": False,
            },
            action_buttons=action_buttons,
            refresh_interval_ms=3000,
            payload_size="full",
        )
