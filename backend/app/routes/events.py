from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.event import ProctoringEventPublic
from app.models.user import UserPublic, UserRole

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/recent", response_model=List[ProctoringEventPublic])
async def recent_events(limit: int = 100, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.proctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only proctors can view events")

    db = get_db()
    cursor = db["proctoring_events"].find({}).sort("timestamp", -1).limit(max(1, min(limit, 500)))
    items = await cursor.to_list(length=500)
    return [ProctoringEventPublic.model_validate(i) for i in items]


@router.get("/mine", response_model=List[ProctoringEventPublic])
async def my_events(limit: int = 200, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    cursor = (
        db["proctoring_events"]
        .find({"student_id": current_user.id})
        .sort("timestamp", -1)
        .limit(max(1, min(limit, 500)))
    )
    items = await cursor.to_list(length=500)
    return [ProctoringEventPublic.model_validate(i) for i in items]


@router.get("/active-alerts")
async def active_alerts(minutes: int = 30, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.proctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only proctors can view alerts")

    since = datetime.now(timezone.utc).timestamp() - (max(1, minutes) * 60)
    since_dt = datetime.fromtimestamp(since, tz=timezone.utc)

    db = get_db()
    cursor = (
        db["proctoring_events"]
        .find({"suspicious": True, "timestamp": {"$gte": since_dt}})
        .sort("timestamp", -1)
        .limit(500)
    )
    items = await cursor.to_list(length=500)
    return {"count": len(items), "alerts": [ProctoringEventPublic.model_validate(i) for i in items]}

