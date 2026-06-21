"""
AXIOM Comms API
Nexxon National | Unclassified

Secure messaging, encryption testing,
and audit chain verification endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.comms.encryption import (
    encrypt_message, decrypt_message,
    sign_message, verify_signature,
    generate_mission_key_package,
)
from app.comms.message_bus import message_bus, MessageType, MessagePriority
from app.comms.audit import audit_chain
from app.api.deps import require_operator, require_commander, require_observer
from app.core.security import TokenData
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("axiom.comms_api")


class SendMessageRequest(BaseModel):
    mission_id: str
    to_callsign: str
    message_type: MessageType
    content: str
    priority: MessagePriority = MessagePriority.ROUTINE


class EncryptRequest(BaseModel):
    mission_id: str
    plaintext: str
    additional_data: Optional[str] = None


@router.post("/message/send", tags=["Comms"])
async def send_secure_message(
    payload: SendMessageRequest,
    current_user: TokenData = Depends(require_operator),
) -> dict:
    """Send an encrypted, signed message between elements."""
    msg = message_bus.send(
        mission_id=payload.mission_id,
        from_callsign=current_user.sub,
        to_callsign=payload.to_callsign,
        message_type=payload.message_type,
        content=payload.content,
        priority=payload.priority,
    )

    audit_chain.log(
        event_type="message_sent",
        actor=current_user.sub,
        mission_id=payload.mission_id,
        summary=f"{current_user.sub} -> {payload.to_callsign}: {payload.message_type}",
        payload={"msg_id": msg.id, "priority": payload.priority},
    )

    return {
        "message_id": msg.id,
        "status": "sent",
        "encrypted": True,
        "signed": True,
        "from": current_user.sub,
        "to": payload.to_callsign,
        "type": payload.message_type,
        "priority": payload.priority,
        "sent_at": msg.sent_at,
    }


@router.get("/message/mission/{mission_id}", tags=["Comms"])
async def get_mission_messages(
    mission_id: str,
    current_user: TokenData = Depends(require_observer),
) -> dict:
    """Get all messages for a mission."""
    msgs = message_bus.get_mission_messages(mission_id, current_user.sub)
    stats = message_bus.get_stats(mission_id)
    return {
        "mission_id": mission_id,
        "message_count": len(msgs),
        "messages": [
            {
                "id": m.id,
                "from": m.from_callsign,
                "to": m.to_callsign,
                "type": m.message_type,
                "priority": m.priority,
                "sent_at": m.sent_at,
                "encrypted": True,
            }
            for m in msgs
        ],
        "stats": stats,
    }


@router.post("/encrypt/test", tags=["Comms"])
async def test_encryption(
    payload: EncryptRequest,
    current_user: TokenData = Depends(require_operator),
) -> dict:
    """
    Encrypt and immediately decrypt a test message.
    Verifies the full encryption cycle and returns timing.
    Used for security integration testing.
    """
    import time
    start = time.perf_counter()

    encrypted = encrypt_message(
        payload.plaintext,
        payload.mission_id,
        payload.additional_data,
    )

    decrypted = decrypt_message(encrypted)
    elapsed_ms = (time.perf_counter() - start) * 1000

    signature = sign_message(payload.plaintext, payload.mission_id)
    verified = verify_signature(payload.plaintext, signature, payload.mission_id)

    return {
        "encryption_algorithm": "AES-256-GCM",
        "hmac_algorithm": "HMAC-SHA256",
        "fips_compliant": True,
        "roundtrip_verified": decrypted == payload.plaintext,
        "signature_verified": verified,
        "processing_ms": round(elapsed_ms, 3),
        "plaintext_length": len(payload.plaintext),
        "ciphertext_length": len(encrypted["ciphertext"]),
        "nonce_bits": 96,
        "key_bits": 256,
        "tag_bits": 128,
    }


@router.get("/keys/mission/{mission_id}", tags=["Comms"])
async def get_key_package(
    mission_id: str,
    current_user: TokenData = Depends(require_commander),
) -> dict:
    """Get key metadata for a mission. Commander only."""
    return generate_mission_key_package(mission_id)


@router.get("/audit/mission/{mission_id}", tags=["Comms"])
async def get_audit_log(
    mission_id: str,
    current_user: TokenData = Depends(require_commander),
) -> dict:
    """Get tamper-evident audit log for a mission. Commander only."""
    log = audit_chain.get_mission_log(mission_id)
    valid, error = audit_chain.verify_chain()
    return {
        "mission_id": mission_id,
        "entry_count": len(log),
        "chain_valid": valid,
        "chain_error": error,
        "entries": log,
    }


@router.get("/audit/verify", tags=["Comms"])
async def verify_audit_chain(
    current_user: TokenData = Depends(require_commander),
) -> dict:
    """Verify the integrity of the entire audit chain."""
    valid, error = audit_chain.verify_chain()
    total = len(audit_chain.get_full_log())
    return {
        "chain_valid": valid,
        "total_entries": total,
        "error": error,
        "message": "Audit chain integrity verified" if valid else f"CHAIN COMPROMISED: {error}",
    }
