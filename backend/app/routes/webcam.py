from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.db.mongo import get_db
from app.models.webcam import WebcamLogPublic
from app.models.user import UserPublic, UserRole

router = APIRouter(prefix="/webcam", tags=["webcam"])


@router.get("/latest", response_model=Optional[WebcamLogPublic])
async def latest_for_session(session_id: str, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    doc = await db["webcam_logs"].find_one({"session_id": session_id}, sort=[("captured_at", -1)])
    if not doc:
        return None

    # student can see their own; proctor can see all
    if current_user.role == UserRole.student and doc.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    return WebcamLogPublic.model_validate(doc)


@router.get("/latest-by-student", response_model=Optional[WebcamLogPublic])
async def latest_for_student(student_id: str, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.proctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only proctors can view")
    db = get_db()
    doc = await db["webcam_logs"].find_one({"student_id": student_id}, sort=[("captured_at", -1)])
    return WebcamLogPublic.model_validate(doc) if doc else None


@router.get("/recent", response_model=List[WebcamLogPublic])
async def recent_logs(
    session_id: Optional[str] = None,
    limit: int = 30,
    current_user: UserPublic = Depends(get_current_user),
):
    db = get_db()
    q = {}
    if session_id:
        q["session_id"] = session_id

    if current_user.role == UserRole.student:
        q["student_id"] = current_user.id

    cursor = db["webcam_logs"].find(q).sort("captured_at", -1).limit(max(1, min(limit, 200)))
    items = await cursor.to_list(length=200)
    return [WebcamLogPublic.model_validate(i) for i in items]

