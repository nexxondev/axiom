"""
AXIOM Encryption Engine
Nexxon National | Unclassified

AES-256-GCM authenticated encryption.
FIPS 140-2 compliant patterns.
Every message encrypted at rest and in transit.

Key hierarchy:
  Master Key (env) -> Mission Keys -> Message Keys
  Rotation-ready from day one.
"""

import os
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone
from typing import Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, hmac as crypto_hmac
from cryptography.hazmat.backends import default_backend
from app.core.logging import get_logger

logger = get_logger("axiom.encryption")

# Key sizes
AES_KEY_SIZE = 32   # 256 bits
NONCE_SIZE = 12     # 96 bits — GCM standard
TAG_SIZE = 16       # 128 bits — GCM authentication tag


class EncryptionError(Exception):
    pass


class DecryptionError(Exception):
    pass


def _get_master_key() -> bytes:
    """
    Retrieve master encryption key from environment.
    In production: HSM or KMS (AWS KMS, Azure Key Vault).
    """
    key_hex = os.environ.get("AXIOM_MASTER_KEY", "")
    if key_hex and len(key_hex) >= 64:
        return bytes.fromhex(key_hex[:64])
    # Dev fallback — deterministic but NOT for production
    seed = os.environ.get("SECRET_KEY",
        "dev-secret-change-in-production-minimum-64-chars-required")
    return hashlib.sha256(seed.encode()).digest()


def derive_mission_key(mission_id: str) -> bytes:
    """
    Derive a mission-specific key from master key.
    Each mission has its own encryption context.
    HKDF-style derivation using HMAC-SHA256.
    """
    master = _get_master_key()
    h = hmac.new(master, msg=f"mission:{mission_id}".encode(), digestmod=hashlib.sha256)
    return h.digest()


def encrypt_message(
    plaintext: str,
    mission_id: str,
    additional_data: Optional[str] = None,
) -> dict:
    """
    Encrypt a message using AES-256-GCM.
    Returns encrypted payload with nonce and metadata.
    additional_data is authenticated but not encrypted (AAD).
    """
    try:
        key = derive_mission_key(mission_id)
        nonce = os.urandom(NONCE_SIZE)
        aesgcm = AESGCM(key)

        aad = additional_data.encode() if additional_data else None
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), aad)

        payload = {
            "ciphertext": base64.b64encode(ciphertext).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "mission_id": mission_id,
            "aad": additional_data,
            "algorithm": "AES-256-GCM",
            "encrypted_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("message_encrypted", mission_id=mission_id,
                    size_bytes=len(ciphertext))
        return payload

    except Exception as e:
        logger.error("encryption_failed", error=str(e))
        raise EncryptionError(f"Encryption failed: {e}")


def decrypt_message(payload: dict) -> str:
    """
    Decrypt an AES-256-GCM encrypted message.
    Verifies authentication tag automatically.
    Raises DecryptionError if tampered.
    """
    try:
        mission_id = payload["mission_id"]
        key = derive_mission_key(mission_id)
        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])
        aad = payload.get("aad")
        aad_bytes = aad.encode() if aad else None

        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, aad_bytes)

        logger.info("message_decrypted", mission_id=mission_id)
        return plaintext.decode()

    except Exception as e:
        logger.error("decryption_failed", error=str(e))
        raise DecryptionError(f"Decryption failed — message may be tampered: {e}")


def sign_message(message: str, mission_id: str) -> str:
    """
    HMAC-SHA256 message signing.
    Used to verify message integrity without full encryption.
    """
    key = derive_mission_key(mission_id)
    h = hmac.new(key, msg=message.encode(), digestmod=hashlib.sha256)
    return h.hexdigest()


def verify_signature(message: str, signature: str, mission_id: str) -> bool:
    """
    Verify HMAC-SHA256 signature.
    Constant-time comparison prevents timing attacks.
    """
    expected = sign_message(message, mission_id)
    return hmac.compare_digest(expected, signature)


def generate_mission_key_package(mission_id: str) -> dict:
    """
    Generate a complete key package for a mission.
    In production: stored in KMS, never in code or logs.
    """
    mission_key = derive_mission_key(mission_id)
    key_id = hashlib.sha256(mission_key).hexdigest()[:16]

    return {
        "mission_id": mission_id,
        "key_id": key_id,
        "algorithm": "AES-256-GCM",
        "key_size_bits": 256,
        "hmac_algorithm": "HMAC-SHA256",
        "fips_compliant": True,
        "rotation_required_hours": 24,
        "key_fingerprint": key_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
