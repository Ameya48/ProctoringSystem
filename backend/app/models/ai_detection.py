from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class AIDetectionType(str, Enum):
    NO_FACE_DETECTED = "no_face_detected"
    MULTIPLE_FACES = "multiple_faces"
    LOOKING_AWAY = "looking_away"
    EXCESSIVE_HEAD_MOVEMENT = "excessive_head_movement"
    FACE_NOT_VISIBLE = "face_not_visible"
    SUSPICIOUS_OBJECT = "suspicious_object"
    ABNORMAL_BEHAVIOR = "abnormal_behavior"


class FaceDetectionResult(BaseModel):
    face_count: int
    face_rects: List[List[int]] = Field(default_factory=list)  # List of [x, y, w, h]
    face_landmarks: Optional[List[List[Tuple[float, float]]]] = None
    head_pose: Optional[Dict[str, float]] = None
    confidence: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIDetectionEvent(BaseModel):
    detection_type: AIDetectionType
    confidence: float = Field(ge=0.0, le=1.0)
    severity: int = Field(ge=0, le=100, default=50)
    details: Dict[str, Any] = Field(default_factory=dict)
    frame_data: Optional[str] = None  # Base64 encoded frame for review
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AIDetectionResult(BaseModel):
    session_id: str
    student_id: str
    exam_id: Optional[str] = None
    frame_timestamp: datetime
    face_detection: FaceDetectionResult
    ai_events: List[AIDetectionEvent] = Field(default_factory=list)
    processing_time_ms: float
    suspicious_score: int = Field(ge=0, le=100, default=0)


class AIDetectionConfig(BaseModel):
    enable_face_detection: bool = True
    enable_head_pose_estimation: bool = True
    enable_multiple_face_detection: bool = True
    enable_looking_away_detection: bool = True
    enable_head_movement_tracking: bool = True
    
    # Detection thresholds
    no_face_threshold_seconds: float = 3.0
    multiple_faces_threshold: int = 2
    looking_away_threshold_degrees: float = 45.0
    head_movement_threshold_pixels: float = 50.0
    head_movement_window_seconds: float = 5.0
    
    # Performance settings
    max_processing_fps: int = 10
    frame_skip_count: int = 2
    confidence_threshold: float = 0.5
    
    # Alert settings
    auto_alert_threshold: int = 70
    event_cooldown_seconds: float = 2.0


class AIAlert(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    session_id: str
    student_id: str
    exam_id: Optional[str] = None
    alert_type: AIDetectionType
    severity: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    frame_snapshot: Optional[str] = None  # Base64 encoded frame
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    resolved: bool = False


class AIAnalytics(BaseModel):
    session_id: str
    total_frames_processed: int
    faces_detected_distribution: Dict[int, int] = Field(default_factory=dict)
    looking_away_events: int = 0
    head_movement_events: int = 0
    no_face_events: int = 0
    multiple_face_events: int = 0
    average_processing_time_ms: float
    peak_suspicious_score: int = 0
    alert_count: int = 0
    session_duration_seconds: float
    compliance_score: float = Field(ge=0.0, le=100.0)  # Overall compliance percentage
