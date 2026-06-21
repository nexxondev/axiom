from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum


class TargetType(str, Enum):
    HVT = "high_value_target"
    HVI = "high_value_individual"
    MATERIAL = "material"
    INFRASTRUCTURE = "infrastructure"
    VEHICLE = "vehicle"
    PERSONNEL = "personnel"
    EQUIPMENT = "equipment"


class TargetStatus(str, Enum):
    NOMINATED = "nominated"
    CONFIRMED = "confirmed"
    DESIGNATED = "designated"
    ENGAGED = "engaged"
    NEUTRALIZED = "neutralized"
    RELEASED = "released"
    DECONFLICTED = "deconflicted"


class ROEStatus(str, Enum):
    COMPLIANT = "compliant"
    HOLD = "hold"
    RESTRICTED = "restricted"
    PROHIBITED = "prohibited"


class TargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    target_type: TargetType
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    altitude_m: Optional[float] = None
    description: Optional[str] = Field(None, max_length=1024)
    intelligence_source: Optional[str] = Field(None, max_length=128)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class TargetCreate(TargetBase):
    mission_id: UUID


class TargetUpdate(BaseModel):
    status: Optional[TargetStatus] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    roe_status: Optional[ROEStatus] = None
    priority_override: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=1024)


class Target(TargetBase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    status: TargetStatus = TargetStatus.NOMINATED
    roe_status: ROEStatus = ROEStatus.COMPLIANT
    priority_score: float = Field(default=0.0, ge=0.0, le=100.0)
    priority_override: Optional[int] = None
    engagement_authority: Optional[str] = None
    designated_asset: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"from_attributes": True}
