from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class WebcamLogInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(min_length=1, max_length=128)
    student_id: str = Field(min_length=1, max_length=128)
    exam_id: Optional[str] = Field(default=None, max_length=64)

    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    saved_path: str
    content_type: str = "image/jpeg"
    size_bytes: int = 0

    frame_width: Optional[int] = None
    frame_height: Optional[int] = None


class WebcamLogPublic(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    student_id: str
    exam_id: Optional[str] = None
    captured_at: datetime
    saved_path: str
    content_type: str
    size_bytes: int
