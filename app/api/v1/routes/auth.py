from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from typing import Optional
from app.core.security import create_access_token, verify_password, decode_token, TokenData
from app.db.models import UserDB
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    callsign: str


class MeResponse(BaseModel):
    callsign: str
    role: str
    permissions: list


async def get_current_user(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)) -> UserDB:
    """Dependency to extract and validate JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    try:
        token_data = decode_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(UserDB).where(UserDB.callsign == token_data.sub))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with callsign and password. Returns JWT token."""
    result = await db.execute(select(UserDB).where(UserDB.callsign == request.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid callsign or password")
    
    access_token = create_access_token(
        subject=user.callsign,
        role=user.role,
        mission_ids=[]
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        callsign=user.callsign
    )


@router.get("/me", response_model=MeResponse)
async def get_current_user_info(current_user: UserDB = Depends(get_current_user)):
    """Get current authenticated user's info. Requires valid JWT in Authorization header."""
    role_permissions = {
        "system": ["*"],
        "commander": ["missions:read", "missions:create", "missions:update", "coa:generate", "coa:approve"],
        "staff": ["missions:read", "coa:generate", "coa:read", "reports:read"],
        "isr": ["intel:read", "reports:create"],
        "operator": ["missions:read", "coa:read"],
        "observer": ["missions:read"]
    }
    
    permissions = role_permissions.get(current_user.role.lower(), [])
    
    return MeResponse(
        callsign=current_user.callsign,
        role=current_user.role,
        permissions=permissions
    )