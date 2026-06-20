"""
AXIOM Core Enumerations
Nexxon National | Unclassified

The controlled vocabulary for all mission entities.
Every status, type, and classification in the system
is defined here — no magic strings anywhere.
"""

from enum import Enum


class MissionStatus(str, Enum):
    PLANNING = "planning"
    BRIEFED = "briefed"
    INFIL = "infil"
    ACTIVE = "active"
    EXFIL = "exfil"
    COMPLETE = "complete"
    ABORTED = "aborted"


class MissionType(str, Enum):
    DA = "direct_action"
    SR = "special_reconnaissance"
    UW = "unconventional_warfare"
    FID = "foreign_internal_defense"
    CASEVAC = "casevac"
    EXFIL = "exfil_only"
    CUSTOM = "custom"


class WaypointType(str, Enum):
    SP = "start_point"
    RP = "release_point"
    OBJ = "objective"
    HLZ = "helicopter_landing_zone"
    PZ = "pickup_zone"
    DZ = "drop_zone"
    CCP = "casualty_collection_point"
    ORP = "objective_rally_point"
    EGRESS = "egress"
    ALTERNATE = "alternate"
    WAYPOINT = "waypoint"


class ThreatType(str, Enum):
    ENEMY_POSITION = "enemy_position"
    AA = "anti_aircraft"
    IED = "ied"
    PATROL = "patrol"
    OBSERVATION_POST = "observation_post"
    VEHICLE = "vehicle"
    UNKNOWN = "unknown"


class ThreatLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssetType(str, Enum):
    GROUND_ELEMENT = "ground_element"
    ISR_DRONE = "isr_drone"
    ATTACK_AIRCRAFT = "attack_aircraft"
    ROTARY_WING = "rotary_wing"
    VEHICLE = "vehicle"
    WATERCRAFT = "watercraft"


class AssetStatus(str, Enum):
    STANDBY = "standby"
    MOVING = "moving"
    ON_STATION = "on_station"
    ENGAGED = "engaged"
    CASUALTY = "casualty"
    EXFIL = "exfil"


class OperatorRole(str, Enum):
    COMMANDER = "commander"
    ASSISTANT_COMMANDER = "assistant_commander"
    MEDIC = "medic"
    COMMS = "comms"
    BREACHER = "breacher"
    SNIPER = "sniper"
    JTAC = "jtac"
    OPERATOR = "operator"


class OperatorStatus(str, Enum):
    ACTIVE = "active"
    INJURED = "injured"
    KIA = "kia"
    MIA = "mia"
    EXFIL = "exfil"


class CoAStatus(str, Enum):
    GENERATED = "generated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"


class CoASource(str, Enum):
    AI_GENERATED = "ai_generated"
    HUMAN_PLANNED = "human_planned"
    AI_ASSISTED = "ai_assisted"


class EventType(str, Enum):
    MISSION_CREATED = "mission_created"
    MISSION_STATUS_CHANGED = "mission_status_changed"
    WAYPOINT_ADDED = "waypoint_added"
    THREAT_DETECTED = "threat_detected"
    THREAT_UPDATED = "threat_updated"
    ASSET_STATUS_CHANGED = "asset_status_changed"
    OPERATOR_STATUS_CHANGED = "operator_status_changed"
    COA_GENERATED = "coa_generated"
    COA_APPROVED = "coa_approved"
    COA_REJECTED = "coa_rejected"
    REPLAN_TRIGGERED = "replan_triggered"
    REPLAN_COMPLETE = "replan_complete"
    COMMS_EVENT = "comms_event"
    SYSTEM_EVENT = "system_event"


class ClassificationLevel(str, Enum):
    UNCLASSIFIED = "U"
    CUI = "CUI"
    SECRET = "S"
    TOP_SECRET = "TS"
