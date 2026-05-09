from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.mongo import get_db
from app.models.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserPublic,
    UserRole,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    db = get_db()
    user_id = str(uuid.uuid4())

    doc = {
        "_id": user_id,
        "email": payload.email.lower(),
        "full_name": payload.full_name,
        "role": payload.role.value if isinstance(payload.role, UserRole) else payload.role,
        "password_hash": hash_password(payload.password),
    }

    try:
        await db["users"].insert_one(doc)
    except Exception:
        # Most common: duplicate email (unique index)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    token = create_access_token(subject=user_id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    db = get_db()
    user = await db["users"].find_one({"email": payload.email.lower()})
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    # Temporarily bypass password verification for demo
    if payload.password != "student123" and payload.password != "proctor123":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    
    # Original password check (temporarily disabled)
    # if not verify_password(payload.password, user.get("password_hash", "")):
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    token = create_access_token(subject=user["_id"])
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserPublic)
async def me(current_user: UserPublic = Depends(get_current_user)):
    return current_user

