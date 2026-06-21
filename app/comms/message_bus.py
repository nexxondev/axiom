"""
AXIOM Secure Message Bus
Nexxon National | Unclassified

Encrypted message passing between assets,
operators, and command elements.
Every message is encrypted, signed, and logged.
"""

from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional
from enum import Enum
from pydantic import BaseModel
from app.comms.encryption import encrypt_message, decrypt_message, sign_message, verify_signature
from app.core.logging import get_logger

logger = get_logger("axiom.message_bus")


class MessageType(str, Enum):
    SITREP = "sitrep"
    ALERT = "alert"
    COA_APPROVAL = "coa_approval"
    REPLAN_REQUEST = "replan_request"
    CASEVAC = "casevac"
    ABORT = "abort"
    COMMS_CHECK = "comms_check"
    INTEL = "intel"


class MessagePriority(str, Enum):
    ROUTINE = "routine"
    PRIORITY = "priority"
    IMMEDIATE = "immediate"
    FLASH = "flash"


class SecureMessage(BaseModel):
    id: str
    mission_id: str
    from_callsign: str
    to_callsign: str
    message_type: MessageType
    priority: MessagePriority
    encrypted_payload: dict
    signature: str
    sent_at: str
    classification: str = "UNCLASSIFIED"


class MessageBus:
    def __init__(self):
        self._messages: list[SecureMessage] = []

    def send(
        self,
        mission_id: str,
        from_callsign: str,
        to_callsign: str,
        message_type: MessageType,
        content: str,
        priority: MessagePriority = MessagePriority.ROUTINE,
    ) -> SecureMessage:
        """
        Send an encrypted, signed message between elements.
        """
        aad = f"{from_callsign}:{to_callsign}:{mission_id}"
        encrypted = encrypt_message(content, mission_id, additional_data=aad)
        signature = sign_message(content, mission_id)

        msg = SecureMessage(
            id=str(uuid4()),
            mission_id=mission_id,
            from_callsign=from_callsign,
            to_callsign=to_callsign,
            message_type=message_type,
            priority=priority,
            encrypted_payload=encrypted,
            signature=signature,
            sent_at=datetime.now(timezone.utc).isoformat(),
        )

        self._messages.append(msg)
        logger.info(
            "message_sent",
            msg_id=msg.id,
            mission_id=mission_id,
            from_cs=from_callsign,
            to_cs=to_callsign,
            type=message_type,
            priority=priority,
        )
        return msg

    def receive(
        self,
        message: SecureMessage,
        mission_id: str,
    ) -> Optional[str]:
        """
        Receive and decrypt a message.
        Verifies signature before decryption.
        Returns None if verification fails.
        """
        try:
            plaintext = decrypt_message(message.encrypted_payload)
            verified = verify_signature(plaintext, message.signature, mission_id)

            if not verified:
                logger.error(
                    "message_verification_failed",
                    msg_id=message.id,
                    mission_id=mission_id,
                )
                return None

            logger.info(
                "message_received",
                msg_id=message.id,
                mission_id=mission_id,
                verified=True,
            )
            return plaintext

        except Exception as e:
            logger.error("message_receive_error", error=str(e))
            return None

    def get_mission_messages(
        self,
        mission_id: str,
        callsign: Optional[str] = None,
    ) -> list[SecureMessage]:
        msgs = [m for m in self._messages if m.mission_id == mission_id]
        if callsign:
            msgs = [m for m in msgs
                    if m.to_callsign == callsign or m.from_callsign == callsign]
        return sorted(msgs, key=lambda m: m.sent_at, reverse=True)

    def get_stats(self, mission_id: str) -> dict:
        msgs = [m for m in self._messages if m.mission_id == mission_id]
        return {
            "total_messages": len(msgs),
            "by_type": {t.value: sum(1 for m in msgs if m.message_type == t)
                        for t in MessageType},
            "by_priority": {p.value: sum(1 for m in msgs if m.priority == p)
                           for p in MessagePriority},
        }


# Global message bus instance
message_bus = MessageBus()
