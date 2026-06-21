"""
AXIOM Adapter Router
Nexxon National | Unclassified

Selects the correct adapter for a given form factor
and transforms mission state into the right payload.
"""

from app.adapters.base import (
    DisplayFormFactor, MissionStateInput, AdapterResponse
)
from app.adapters.tablet import TabletAdapter
from app.adapters.hud import HUDAdapter
from app.adapters.wrist import WristAdapter

_ADAPTERS = {
    DisplayFormFactor.TABLET: TabletAdapter(),
    DisplayFormFactor.HUD: HUDAdapter(),
    DisplayFormFactor.WRIST: WristAdapter(),
    DisplayFormFactor.DESKTOP: TabletAdapter(),  # Desktop uses tablet layout
}


def get_adapter(form_factor: DisplayFormFactor):
    return _ADAPTERS.get(form_factor, TabletAdapter())


def render_for_display(
    state: MissionStateInput,
    form_factor: DisplayFormFactor,
) -> AdapterResponse:
    adapter = get_adapter(form_factor)
    return adapter.render(state)
