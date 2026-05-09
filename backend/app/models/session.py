from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    active = "active"
    ended = "ended"


class SessionInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    exam_id: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=128)
    status: SessionStatus = SessionStatus.active
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None


class StartExamRequest(BaseModel):
    exam_id: str = Field(min_length=1, max_length=64)


class EndExamRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)


class SessionPublic(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    exam_id: str
    student_id: str
    status: SessionStatus
    started_at: datetime
    ended_at: Optional[datetime] = None

