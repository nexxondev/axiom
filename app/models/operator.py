"""
AXIOM Operator Model
Nexxon National | Unclassified

The human element. Role, status, asset assignment.
"""

from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from app.models.enums import OperatorRole, OperatorStatus


class OperatorBase(BaseModel):
    callsign: str = Field(..., min_length=1, max_length=32)
    role: OperatorRole
    asset_id: Optional[UUID] = None


class OperatorCreate(OperatorBase):
    mission_id: UUID


class OperatorUpdate(BaseModel):
    status: Optional[OperatorStatus] = None
    asset_id: Optional[UUID] = None


class Operator(OperatorBase):
    id: UUID = Field(default_factory=uuid4)
    mission_id: UUID
    status: OperatorStatus = OperatorStatus.ACTIVE

    model_config = {"from_attributes": True}
