from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    screen_share_started = "screen_share_started"
    screen_share_stopped = "screen_share_stopped"
    tab_hidden = "tab_hidden"
    tab_visible = "tab_visible"
    window_blur = "window_blur"
    window_focus = "window_focus"
    fullscreen_exited = "fullscreen_exited"
    idle = "idle"
    activity_resumed = "activity_resumed"


class ProctoringEventInDB(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str = Field(min_length=1, max_length=128)
    student_id: str = Field(min_length=1, max_length=128)
    exam_id: Optional[str] = Field(default=None, max_length=64)

    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    details: Dict[str, Any] = Field(default_factory=dict)

    suspicious: bool = False
    severity: int = 0  # 0..100


class ProctoringEventIngest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    exam_id: Optional[str] = Field(default=None, max_length=64)
    event_type: EventType
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ProctoringEventPublic(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    student_id: str
    exam_id: Optional[str] = None
    event_type: EventType
    timestamp: datetime
    details: Dict[str, Any]
    suspicious: bool
    severity: int

