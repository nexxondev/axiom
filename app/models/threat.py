"""
AXIOM Threat Model
Nexxon National | Unclassified

Enemy positions, IEDs, AA, patrols.
Confidence score drives AI weighting in replanning.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import ThreatType, ThreatLevel


class ThreatBase(BaseModel):
    threat_type: ThreatType
    threat_level: ThreatLevel
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    radius_m: float = Field(default=100.0, ge=0.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    source: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = Field(None, max_length=512)
    is_active: bool = True


class ThreatCreate(ThreatBase):
    mission_id: UUID


class ThreatUpdate(BaseModel):
    threat_level: Optional[ThreatLevel] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class Threat(ThreatBase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True}
