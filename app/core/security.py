"""
AXIOM Security Layer
Nexxon National | Unclassified

JWT token creation and validation.
RBAC role definitions.
Designed for future CAC/PIV integration.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.core.config import settings


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# RBAC Roles — maps to real SOF command structure
class Role:
    SYSTEM = "system"          # Internal service calls
    COMMANDER = "commander"    # Full access
    STAFF = "staff"            # Planning access, no execution
    OPERATOR = "operator"      # Own mission only
    ISR = "isr"                # Intel feed write, read-only on missions
    OBSERVER = "observer"      # Read-only


ROLE_HIERARCHY = {
    Role.SYSTEM: 100,
    Role.COMMANDER: 90,
    Role.STAFF: 70,
    Role.ISR: 60,
    Role.OPERATOR: 50,
    Role.OBSERVER: 10,
}


class TokenData(BaseModel):
    sub: str                    # User identifier / callsign
    role: str
    mission_ids: list[str] = [] # Scoped mission access
    exp: Optional[datetime] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    role: str


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    role: str,
    mission_ids: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "mission_ids": mission_ids or [],
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "axiom.nexxonnational.com",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    return TokenData(
        sub=payload["sub"],
        role=payload["role"],
        mission_ids=payload.get("mission_ids", []),
    )


def has_role(user_role: str, required_role: str) -> bool:
    """Check if user_role meets or exceeds required_role."""
    return ROLE_HIERARCHY.get(user_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
