"""
AXIOM Mission Model
Nexxon National | Unclassified

The top-level operational entity. Everything else
belongs to a Mission.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import (
    MissionStatus,
    MissionType,
    ClassificationLevel,
)


class MissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    mission_type: MissionType
    classification: ClassificationLevel = ClassificationLevel.UNCLASSIFIED
    description: Optional[str] = Field(None, max_length=1024)
    operational_area: Optional[str] = Field(None, max_length=256)
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


class MissionCreate(MissionBase):
    pass


class MissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    status: Optional[MissionStatus] = None
    description: Optional[str] = None
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None


class Mission(MissionBase):
    id: UUID = Field(default_factory=uuid4)
    status: MissionStatus = MissionStatus.PLANNING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}
