from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.core.ws import sessions_ws_manager
from app.db.mongo import get_db
from app.models.session import (
    EndExamRequest,
    SessionPublic,
    SessionStatus,
    StartExamRequest,
)
from app.models.user import UserPublic, UserRole

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=SessionPublic)
async def start_exam(payload: StartExamRequest, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can start exams")

    db = get_db()
    existing = await db["sessions"].find_one(
        {"student_id": current_user.id, "exam_id": payload.exam_id, "status": SessionStatus.active.value}
    )
    if existing:
        return SessionPublic.model_validate(existing)

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc: Dict[str, Any] = {
        "_id": session_id,
        "exam_id": payload.exam_id,
        "student_id": current_user.id,
        "status": SessionStatus.active.value,
        "started_at": now,
        "ended_at": None,
    }
    await db["sessions"].insert_one(doc)
    await sessions_ws_manager.broadcast({"type": "session_started", "session": doc})
    return SessionPublic.model_validate(doc)


@router.post("/end", response_model=SessionPublic)
async def end_exam(payload: EndExamRequest, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    session = await db["sessions"].find_one({"_id": payload.session_id})
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # student can end their own session; proctor can end any
    if current_user.role == UserRole.student and session.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to end this session")

    if session.get("status") == SessionStatus.ended.value:
        return SessionPublic.model_validate(session)

    now = datetime.now(timezone.utc)
    await db["sessions"].update_one(
        {"_id": payload.session_id},
        {"$set": {"status": SessionStatus.ended.value, "ended_at": now}},
    )
    session["status"] = SessionStatus.ended.value
    session["ended_at"] = now
    await sessions_ws_manager.broadcast({"type": "session_ended", "session": session})
    return SessionPublic.model_validate(session)


@router.get("/active", response_model=List[SessionPublic])
async def list_active_sessions(current_user: UserPublic = Depends(get_current_user)):
    # both roles can view active sessions (simple version)
    db = get_db()
    cursor = db["sessions"].find({"status": SessionStatus.active.value}).sort("started_at", -1)
    sessions = await cursor.to_list(length=200)
    return [SessionPublic.model_validate(s) for s in sessions]


@router.get("/active-students")
async def active_students(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    sessions = await db["sessions"].find({"status": SessionStatus.active.value}).to_list(length=2000)
    student_ids = sorted({s.get("student_id") for s in sessions if s.get("student_id")})
    return {"active_students": student_ids, "count": len(student_ids)}

