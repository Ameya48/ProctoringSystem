from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.core.deps import get_current_user
from app.core.recording_service import (
    append_chunk,
    finalize_upload,
    recording_final_path,
    recording_temp_path,
    safe_ext_from_mime,
)
from app.db.mongo import get_db
from app.models.recording import (
    RecordingCompleteRequest,
    RecordingInitRequest,
    RecordingInitResponse,
    RecordingPublic,
    RecordingStatus,
)
from app.models.user import UserPublic, UserRole

router = APIRouter(prefix="/recordings", tags=["recordings"])


def _storage_dir() -> str:
    # backend/app/.. -> backend/
    from app.main import _storage_dir as sd  # type: ignore

    return sd


def _media_url_for_path(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    sd = _storage_dir()
    try:
        rel = os.path.relpath(path, sd)
    except Exception:
        return None
    return f"/media/{rel.replace(os.sep, '/')}"


@router.post("/init", response_model=RecordingInitResponse)
async def init_recording(payload: RecordingInitRequest, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only students can record")

    db = get_db()
    session = await db["sessions"].find_one({"_id": payload.session_id})
    if not session or session.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid session")

    recording_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    doc: Dict[str, Any] = {
        "_id": recording_id,
        "session_id": payload.session_id,
        "student_id": current_user.id,
        "exam_id": payload.exam_id,
        "status": RecordingStatus.uploading.value,
        "started_at": now,
        "ended_at": None,
        "mime_type": payload.mime_type or "video/webm",
        "filename": None,
        "file_path": None,
        "size_bytes": 0,
        "duration_seconds": None,
        "flagged_seconds": [],
    }
    await db["recordings"].insert_one(doc)

    return RecordingInitResponse(
        recording_id=recording_id,
        upload_url=f"/recordings/{recording_id}/chunk",
        complete_url=f"/recordings/complete",
    )


@router.post("/{recording_id}/chunk")
async def upload_chunk(
    recording_id: str,
    chunk: UploadFile = File(...),
    offset: int = Form(...),
    current_user: UserPublic = Depends(get_current_user),
):
    """
    Efficient upload for large files: send chunks sequentially.
    Client provides `offset` (starting byte index). Server appends; for MVP we enforce sequential offsets.
    """
    db = get_db()
    rec = await db["recordings"].find_one({"_id": recording_id})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    if current_user.role != UserRole.student or rec.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    if rec.get("status") != RecordingStatus.uploading.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Recording not in uploading state")

    expected = int(rec.get("size_bytes") or 0)
    if int(offset) != expected:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Unexpected offset", "expected": expected, "got": int(offset)},
        )

    temp_path = recording_temp_path(_storage_dir(), recording_id)
    data = await chunk.read()
    written = append_chunk(temp_path, data)

    await db["recordings"].update_one({"_id": recording_id}, {"$inc": {"size_bytes": written}})
    return {"ok": True, "written": written, "new_size": expected + written}


@router.post("/complete", response_model=RecordingPublic)
async def complete_recording(payload: RecordingCompleteRequest, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    rec = await db["recordings"].find_one({"_id": payload.recording_id})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    if current_user.role != UserRole.student or rec.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    mime = rec.get("mime_type") or "video/webm"
    ext = safe_ext_from_mime(mime)
    temp_path = recording_temp_path(_storage_dir(), payload.recording_id)
    final_path = recording_final_path(_storage_dir(), payload.recording_id, ext=ext)

    ok, err = finalize_upload(temp_path, final_path)
    if not ok:
        await db["recordings"].update_one(
            {"_id": payload.recording_id},
            {"$set": {"status": RecordingStatus.failed.value}},
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Finalize failed: {err}")

    ended_at = payload.ended_at or datetime.now(timezone.utc)
    duration = payload.duration_seconds

    # compute flagged timestamps from suspicious events during this window (best-effort)
    flagged_seconds: List[float] = []
    try:
        started_at = rec.get("started_at")
        if started_at:
            cursor = db["proctoring_events"].find(
                {
                    "session_id": rec.get("session_id"),
                    "suspicious": True,
                    "timestamp": {"$gte": started_at, "$lte": ended_at},
                }
            )
            events = await cursor.to_list(length=5000)
            for ev in events:
                ts = ev.get("timestamp")
                if ts and started_at:
                    delta = (ts - started_at).total_seconds()
                    if delta >= 0:
                        flagged_seconds.append(round(float(delta), 2))
            flagged_seconds = sorted(set(flagged_seconds))
    except Exception:
        flagged_seconds = []

    await db["recordings"].update_one(
        {"_id": payload.recording_id},
        {
            "$set": {
                "status": RecordingStatus.ready.value,
                "ended_at": ended_at,
                "duration_seconds": duration,
                "filename": os.path.basename(final_path),
                "file_path": final_path,
                "flagged_seconds": flagged_seconds,
            }
        },
    )

    rec2 = await db["recordings"].find_one({"_id": payload.recording_id})
    media_url = _media_url_for_path(rec2.get("file_path"))
    rec2["media_url"] = media_url
    return RecordingPublic.model_validate(rec2)


@router.get("/mine", response_model=List[RecordingPublic])
async def my_recordings(current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    q = {"student_id": current_user.id}
    cursor = db["recordings"].find(q).sort("started_at", -1).limit(200)
    items = await cursor.to_list(length=200)
    for it in items:
        it["media_url"] = _media_url_for_path(it.get("file_path"))
    return [RecordingPublic.model_validate(i) for i in items]


@router.get("/all", response_model=List[RecordingPublic])
async def all_recordings(limit: int = 200, current_user: UserPublic = Depends(get_current_user)):
    if current_user.role != UserRole.proctor:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only proctors can view recordings")
    db = get_db()
    cursor = db["recordings"].find({}).sort("started_at", -1).limit(max(1, min(limit, 500)))
    items = await cursor.to_list(length=500)
    for it in items:
        it["media_url"] = _media_url_for_path(it.get("file_path"))
    return [RecordingPublic.model_validate(i) for i in items]


@router.get("/{recording_id}", response_model=RecordingPublic)
async def get_recording(recording_id: str, current_user: UserPublic = Depends(get_current_user)):
    db = get_db()
    rec = await db["recordings"].find_one({"_id": recording_id})
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recording not found")

    if current_user.role == UserRole.student and rec.get("student_id") != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    rec["media_url"] = _media_url_for_path(rec.get("file_path"))
    return RecordingPublic.model_validate(rec)

