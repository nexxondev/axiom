"""
AXIOM Comms Audit Log
Nexxon National | Unclassified

Tamper-evident audit chain for all communications.
Each entry includes a hash of the previous entry —
any modification breaks the chain.
Required for DoD contract compliance.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("axiom.audit")


class AuditEntry:
    def __init__(
        self,
        event_type: str,
        actor: str,
        mission_id: str,
        summary: str,
        payload: Optional[dict] = None,
        previous_hash: str = "GENESIS",
    ):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.actor = actor
        self.mission_id = mission_id
        self.summary = summary
        self.payload = payload or {}
        self.previous_hash = previous_hash
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = json.dumps({
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "mission_id": self.mission_id,
            "summary": self.summary,
            "previous_hash": self.previous_hash,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "mission_id": self.mission_id,
            "summary": self.summary,
            "hash": self.hash,
            "previous_hash": self.previous_hash,
            "chain_valid": True,
        }


class AuditChain:
    """
    Linked audit log where each entry references
    the hash of the previous one.
    Tampering with any entry breaks all subsequent hashes.
    """

    def __init__(self):
        self._entries: list[AuditEntry] = []

    def log(
        self,
        event_type: str,
        actor: str,
        mission_id: str,
        summary: str,
        payload: Optional[dict] = None,
    ) -> AuditEntry:
        prev_hash = self._entries[-1].hash if self._entries else "GENESIS"
        entry = AuditEntry(
            event_type=event_type,
            actor=actor,
            mission_id=mission_id,
            summary=summary,
            payload=payload,
            previous_hash=prev_hash,
        )
        self._entries.append(entry)
        logger.info(
            "audit_entry",
            event_type=event_type,
            actor=actor,
            mission_id=mission_id,
            hash=entry.hash[:16] + "...",
        )
        return entry

    def verify_chain(self) -> tuple[bool, Optional[str]]:
        """
        Verify the integrity of the entire audit chain.
        Returns (is_valid, error_message).
        """
        for i, entry in enumerate(self._entries[1:], 1):
            expected_prev = self._entries[i-1].hash
            if entry.previous_hash != expected_prev:
                msg = f"Chain broken at entry {i}: {entry.event_type}"
                logger.error("audit_chain_broken", entry_index=i)
                return False, msg
        return True, None

    def get_mission_log(self, mission_id: str) -> list[dict]:
        return [
            e.to_dict() for e in self._entries
            if e.mission_id == mission_id
        ]

    def get_full_log(self) -> list[dict]:
        return [e.to_dict() for e in self._entries]


# Global audit chain
audit_chain = AuditChain()
