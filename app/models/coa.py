"""
AXIOM Course of Action Model
Nexxon National | Unclassified

AI-generated or human-planned mission options.
The CoA is the output of the replanning engine.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import CoAStatus, CoASource


class CoABase(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    source: CoASource
    summary: str = Field(..., max_length=2048)
    risk_level: str = Field(..., max_length=32)
    estimated_duration_min: Optional[int] = None
    waypoints: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: Optional[str] = Field(None, max_length=4096)


class CoACreate(CoABase):
    mission_id: UUID


class CoAUpdate(BaseModel):
    status: Optional[CoAStatus] = None
    commander_notes: Optional[str] = Field(None, max_length=1024)


class CoA(CoABase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    status: CoAStatus = CoAStatus.GENERATED
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    commander_notes: Optional[str] = None

    model_config = {"from_attributes": True}
