"""
AXIOM SQLAlchemy ORM Models
Nexxon National | Unclassified

Database table definitions. Mirror the Pydantic
models in app/models/ but are the persistence layer.
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, JSON, ForeignKey, Text
from sqlalchemy.dialects.sqlite import TEXT
from datetime import datetime, timezone
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class MissionDB(Base):
    __tablename__ = "missions"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    mission_type = Column(String(64), nullable=False)
    status = Column(String(32), default="planning")
    classification = Column(String(8), default="U")
    description = Column(Text, nullable=True)
    operational_area = Column(String(256), nullable=True)
    planned_start = Column(DateTime, nullable=True)
    planned_end = Column(DateTime, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WaypointDB(Base):
    __tablename__ = "waypoints"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    name = Column(String(64), nullable=False)
    waypoint_type = Column(String(32), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=True)
    sequence = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    is_alternate = Column(Boolean, default=False)


class ThreatDB(Base):
    __tablename__ = "threats"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    threat_type = Column(String(64), nullable=False)
    threat_level = Column(String(32), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_m = Column(Float, default=100.0)
    confidence = Column(Float, default=0.8)
    source = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    detected_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class AssetDB(Base):
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    callsign = Column(String(32), nullable=False)
    asset_type = Column(String(64), nullable=False)
    status = Column(String(32), default="standby")
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)


class OperatorDB(Base):
    __tablename__ = "operators"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    callsign = Column(String(32), nullable=False)
    role = Column(String(32), nullable=False)
    status = Column(String(32), default="active")
    asset_id = Column(String(36), nullable=True)


class CoADB(Base):
    __tablename__ = "coas"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    title = Column(String(128), nullable=False)
    source = Column(String(32), nullable=False)
    summary = Column(Text, nullable=False)
    risk_level = Column(String(32), nullable=False)
    estimated_duration_min = Column(Integer, nullable=True)
    waypoints = Column(JSON, default=list)
    reasoning = Column(Text, nullable=True)
    status = Column(String(32), default="generated")
    commander_notes = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=utcnow)


class MissionEventDB(Base):
    __tablename__ = "mission_events"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    classification = Column(String(8), default="U")
    actor = Column(String(64), nullable=True)
    summary = Column(String(512), nullable=False)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


class TargetDB(Base):
    __tablename__ = "targets"

    id = Column(String(36), primary_key=True)
    mission_id = Column(String(36), ForeignKey("missions.id"), nullable=False)
    name = Column(String(128), nullable=False)
    target_type = Column(String(64), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_m = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    intelligence_source = Column(String(128), nullable=True)
    confidence = Column(Float, default=0.7)
    status = Column(String(32), default="nominated")
    roe_status = Column(String(32), default="compliant")
    priority_score = Column(Float, default=0.0)
    priority_override = Column(Integer, nullable=True)
    engagement_authority = Column(String(64), nullable=True)
    designated_asset = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    callsign = Column(String(32), unique=True, nullable=False)
    role = Column(String(32), nullable=False)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    last_login = Column(DateTime, nullable=True)
