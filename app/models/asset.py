"""
AXIOM Asset Model
Nexxon National | Unclassified

Friendly units, vehicles, aircraft, drones.
"""

from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import AssetType, AssetStatus


class AssetBase(BaseModel):
    callsign: str = Field(..., min_length=1, max_length=32)
    asset_type: AssetType
    description: Optional[str] = Field(None, max_length=256)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class AssetCreate(AssetBase):
    mission_id: UUID


class AssetUpdate(BaseModel):
    status: Optional[AssetStatus] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class Asset(AssetBase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    status: AssetStatus = AssetStatus.STANDBY

    model_config = {"from_attributes": True}
