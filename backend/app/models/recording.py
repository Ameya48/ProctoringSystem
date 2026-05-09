from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RecordingStatus(str, Enum):
    uploading = "uploading"
    ready = "ready"
    failed = "failed"


class RecordingInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(min_length=1, max_length=128)
    student_id: str = Field(min_length=1, max_length=128)
    exam_id: Optional[str] = Field(default=None, max_length=64)

    status: RecordingStatus = RecordingStatus.uploading
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    mime_type: str = "video/webm"
    filename: Optional[str] = None
    file_path: Optional[str] = None
    size_bytes: int = 0
    duration_seconds: Optional[float] = None

    flagged_seconds: List[float] = Field(default_factory=list)


class RecordingInitRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    exam_id: Optional[str] = Field(default=None, max_length=64)
    mime_type: str = "video/webm"


class RecordingInitResponse(BaseModel):
    recording_id: str
    upload_url: str
    complete_url: str


class RecordingCompleteRequest(BaseModel):
    recording_id: str = Field(min_length=1, max_length=128)
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class RecordingPublic(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    student_id: str
    exam_id: Optional[str] = None
    status: RecordingStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    mime_type: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    media_url: Optional[str] = None
    flagged_seconds: List[float] = Field(default_factory=list)

