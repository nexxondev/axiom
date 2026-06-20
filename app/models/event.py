"""
AXIOM Mission Event Model
Nexxon National | Unclassified

Immutable audit log. Every significant action
in AXIOM creates an event. Non-negotiable for
government contracts.
"""

from datetime import datetime
from typing import Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import EventType, ClassificationLevel


class MissionEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    event_type: EventType
    classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED
    actor: Optional[str] = Field(None, max_length=64)
    summary: str = Field(..., max_length=512)
    payload: Optional[dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
