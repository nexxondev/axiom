"""
AXIOM Waypoint Model
Nexxon National | Unclassified

A point in space with tactical meaning.
Lat/lon/alt plus type, sequence, and notes.
"""

from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import WaypointType


class WaypointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    waypoint_type: WaypointType
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude_m: Optional[float] = Field(None, ge=-500.0, le=15000.0)
    sequence: int = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=512)
    is_alternate: bool = False


class WaypointCreate(WaypointBase):
    mission_id: UUID


class Waypoint(WaypointBase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID

    model_config = {"from_attributes": True}
