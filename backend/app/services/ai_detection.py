from __future__ import annotations

import asyncio
import base64
import cv2
import mediapipe as mp
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
import logging
from collections import deque
import json

from app.models.ai_detection import (
    AIDetectionConfig,
    AIDetectionEvent,
    AIDetectionResult,
    AIDetectionType,
    AIAlert,
    FaceDetectionResult,
)
from app.services.performance import get_performance_monitor

logger = logging.getLogger(__name__)


class AIDetectionService:
    def __init__(self, config: AIDetectionConfig):
        self.config = config
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize MediaPipe models
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=config.confidence_threshold
        )
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=config.confidence_threshold,
            min_tracking_confidence=config.confidence_threshold
        )
        
        # Tracking state
        self.session_states: Dict[str, Dict[str, Any]] = {}
        self.last_events: Dict[str, Dict[str, datetime]] = {}
        
        # Performance optimization
        self.frame_counter = 0
        self.last_process_time = datetime.now(timezone.utc)
        
    async def process_frame(self, 
                          session_id: str, 
                          student_id: str, 
                          exam_id: Optional[str],
                          frame_data: bytes,
                          frame_timestamp: datetime) -> AIDetectionResult:
        """Process a single frame for AI detection"""
        start_time = datetime.now(timezone.utc)
        
        # Frame skip for performance
        self.frame_counter += 1
        if self.frame_counter % (self.config.frame_skip_count + 1) != 0:
            return self._create_empty_result(session_id, student_id, exam_id, frame_timestamp, start_time)
        
        try:
            # Decode frame
            frame = self._decode_frame(frame_data)
            if frame is None:
                return self._create_empty_result(session_id, student_id, exam_id, frame_timestamp, start_time)
            
            # Initialize session state if needed
            self._initialize_session_state(session_id)
            
            # Perform face detection
            face_detection_result = await self._detect_faces(frame, frame_timestamp)
            
            # Perform AI event detection
            ai_events = await self._detect_ai_events(
                session_id, frame, face_detection_result, frame_timestamp
            )
            
            # Calculate suspicious score
            suspicious_score = self._calculate_suspicious_score(ai_events)
            
            # Update session state
            self._update_session_state(session_id, face_detection_result, ai_events)
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Record performance metrics
            monitor = get_performance_monitor()
            monitor.record_frame_processing(processing_time)
            
            return AIDetectionResult(
                session_id=session_id,
                student_id=student_id,
                exam_id=exam_id,
                frame_timestamp=frame_timestamp,
                face_detection=face_detection_result,
                ai_events=ai_events,
                processing_time_ms=processing_time,
                suspicious_score=suspicious_score
            )
            
        except Exception as e:
            logger.error(f"Error processing frame for session {session_id}: {e}")
            return self._create_empty_result(session_id, student_id, exam_id, frame_timestamp, start_time)
    
    def _decode_frame(self, frame_data: bytes) -> Optional[np.ndarray]:
        """Decode frame data to numpy array"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logger.error(f"Error decoding frame: {e}")
            return None
    
    async def _detect_faces(self, frame: np.ndarray, timestamp: datetime) -> FaceDetectionResult:
        """Detect faces in frame using MediaPipe"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detection.process(rgb_frame)
            
            face_count = 0
            face_rects = []
            face_landmarks = []
            head_poses = []
            
            if results.detections:
                face_count = len(results.detections)
                
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box
                    h, w, _ = frame.shape
                    x, y, w_box, h_box = int(bbox.xmin * w), int(bbox.ymin * h), int(bbox.width * w), int(bbox.height * h)
                    face_rects.append([x, y, w_box, h_box])
                    
                    # Get face landmarks for head pose
                    if self.config.enable_head_pose_estimation:
                        landmarks = self._get_face_landmarks(rgb_frame, detection)
                        if landmarks:
                            face_landmarks.append(landmarks)
                            head_pose = self._estimate_head_pose(landmarks, frame.shape)
                            head_poses.append(head_pose)
            
            avg_confidence = np.mean([detection.score[0] for detection in results.detections]) if results.detections else 0.0
            
            return FaceDetectionResult(
                face_count=face_count,
                face_rects=face_rects,
                face_landmarks=face_landmarks if len(face_landmarks) > 0 else None,
                head_pose=head_poses[0] if head_poses else None,
                confidence=float(avg_confidence),
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error in face detection: {e}")
            return FaceDetectionResult(
                face_count=0,
                confidence=0.0,
                timestamp=timestamp
            )
    
    def _get_face_landmarks(self, rgb_frame: np.ndarray, detection) -> Optional[List[Tuple[float, float]]]:
        """Get detailed face landmarks for head pose estimation"""
        try:
            results = self.face_mesh.process(rgb_frame)
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0]
                return [(lm.x, lm.y) for lm in landmarks.landmark]
        except Exception as e:
            logger.error(f"Error getting face landmarks: {e}")
        return None
    
    def _estimate_head_pose(self, landmarks: List[Tuple[float, float]], frame_shape: Tuple[int, int, int]) -> Dict[str, float]:
        """Estimate head pose from face landmarks"""
        try:
            # Simple head pose estimation using key facial landmarks
            # Using nose tip and eye centers for yaw estimation
            h, w, _ = frame_shape
            
            # Key landmark indices for MediaPipe face mesh
            nose_tip = landmarks[1]  # Nose tip
            left_eye_center = ((landmarks[33][0] + landmarks[7][0]) / 2, (landmarks[33][1] + landmarks[7][1]) / 2)
            right_eye_center = ((landmarks[362][0] + landmarks[263][0]) / 2, (landmarks[362][1] + landmarks[263][1]) / 2)
            
            # Calculate yaw (left-right rotation)
            eye_center_x = (left_eye_center[0] + right_eye_center[0]) / 2
            yaw_offset = (nose_tip[0] - eye_center_x) * w
            
            # Convert to degrees (approximate)
            yaw_degrees = np.degrees(np.arcsin(np.clip(yaw_offset / 100, -1, 1)))
            
            return {
                "yaw": float(yaw_degrees),
                "pitch": 0.0,  # Could be estimated with more complex calculations
                "roll": 0.0    # Could be estimated with more complex calculations
            }
        except Exception as e:
            logger.error(f"Error estimating head pose: {e}")
            return {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
    
    async def _detect_ai_events(self, 
                               session_id: str, 
                               frame: np.ndarray,
                               face_detection: FaceDetectionResult, 
                               timestamp: datetime) -> List[AIDetectionEvent]:
        """Detect AI events based on face detection results"""
        events = []
        session_state = self.session_states[session_id]
        
        # Check for no face detected
        if self.config.enable_face_detection and face_detection.face_count == 0:
            if self._should_trigger_event(session_id, AIDetectionType.NO_FACE_DETECTED, timestamp):
                events.append(AIDetectionEvent(
                    detection_type=AIDetectionType.NO_FACE_DETECTED,
                    confidence=0.8,
                    severity=60,
                    details={"duration_seconds": self._get_no_face_duration(session_id)},
                    frame_data=self._encode_frame(frame)
                ))
        
        # Check for multiple faces
        elif self.config.enable_multiple_face_detection and face_detection.face_count >= self.config.multiple_faces_threshold:
            if self._should_trigger_event(session_id, AIDetectionType.MULTIPLE_FACES, timestamp):
                events.append(AIDetectionEvent(
                    detection_type=AIDetectionType.MULTIPLE_FACES,
                    confidence=0.9,
                    severity=80,
                    details={"face_count": face_detection.face_count, "face_rects": face_detection.face_rects},
                    frame_data=self._encode_frame(frame)
                ))
        
        # Check for looking away
        if (self.config.enable_looking_away_detection and 
            face_detection.head_pose and 
            abs(face_detection.head_pose.get("yaw", 0)) > self.config.looking_away_threshold_degrees):
            
            if self._should_trigger_event(session_id, AIDetectionType.LOOKING_AWAY, timestamp):
                events.append(AIDetectionEvent(
                    detection_type=AIDetectionType.LOOKING_AWAY,
                    confidence=0.7,
                    severity=40,
                    details={"head_pose": face_detection.head_pose, "threshold": self.config.looking_away_threshold_degrees},
                    frame_data=self._encode_frame(frame)
                ))
        
        # Check for excessive head movement
        if self.config.enable_head_movement_tracking:
            movement_event = self._detect_head_movement(session_id, face_detection, timestamp, frame)
            if movement_event:
                events.append(movement_event)
        
        return events
    
    def _detect_head_movement(self, 
                             session_id: str, 
                             face_detection: FaceDetectionResult, 
                             timestamp: datetime,
                             frame: np.ndarray) -> Optional[AIDetectionEvent]:
        """Detect excessive head movement over time"""
        if not face_detection.face_rects or len(face_detection.face_rects) == 0:
            return None
        
        session_state = self.session_states[session_id]
        current_face_center = self._get_face_center(face_detection.face_rects[0])
        
        # Track face positions over time
        if "face_positions" not in session_state:
            session_state["face_positions"] = deque(maxlen=30)  # Track last 30 positions
        
        session_state["face_positions"].append({
            "position": current_face_center,
            "timestamp": timestamp
        })
        
        # Check for excessive movement
        if len(session_state["face_positions"]) >= 10:
            movement = self._calculate_movement_intensity(session_state["face_positions"])
            if movement > self.config.head_movement_threshold_pixels:
                if self._should_trigger_event(session_id, AIDetectionType.EXCESSIVE_HEAD_MOVEMENT, timestamp):
                    return AIDetectionEvent(
                        detection_type=AIDetectionType.EXCESSIVE_HEAD_MOVEMENT,
                        confidence=0.6,
                        severity=30,
                        details={"movement_intensity": movement, "threshold": self.config.head_movement_threshold_pixels},
                        frame_data=self._encode_frame(frame)
                    )
        
        return None
    
    def _get_face_center(self, face_rect: List[int]) -> Tuple[float, float]:
        """Get center point of face rectangle"""
        x, y, w, h = face_rect
        return (x + w / 2, y + h / 2)
    
    def _calculate_movement_intensity(self, positions: deque) -> float:
        """Calculate movement intensity from face positions"""
        if len(positions) < 2:
            return 0.0
        
        total_movement = 0.0
        prev_pos = positions[0]["position"]
        
        for pos_data in list(positions)[1:]:
            current_pos = pos_data["position"]
            distance = np.sqrt((current_pos[0] - prev_pos[0])**2 + (current_pos[1] - prev_pos[1])**2)
            total_movement += distance
            prev_pos = current_pos
        
        return total_movement
    
    def _should_trigger_event(self, session_id: str, event_type: AIDetectionType, timestamp: datetime) -> bool:
        """Check if event should be triggered based on cooldown"""
        if session_id not in self.last_events:
            self.last_events[session_id] = {}
        
        last_event_time = self.last_events[session_id].get(event_type.value)
        if last_event_time is None:
            self.last_events[session_id][event_type.value] = timestamp
            return True
        
        time_diff = (timestamp - last_event_time).total_seconds()
        if time_diff >= self.config.event_cooldown_seconds:
            self.last_events[session_id][event_type.value] = timestamp
            return True
        
        return False
    
    def _get_no_face_duration(self, session_id: str) -> float:
        """Get duration of no face detection"""
        session_state = self.session_states[session_id]
        if "no_face_start_time" in session_state:
            duration = (datetime.now(timezone.utc) - session_state["no_face_start_time"]).total_seconds()
            return duration
        return 0.0
    
    def _encode_frame(self, frame: np.ndarray) -> str:
        """Encode frame to base64 string"""
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            return base64.b64encode(frame_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return ""
    
    def _calculate_suspicious_score(self, ai_events: List[AIDetectionEvent]) -> int:
        """Calculate overall suspicious score from events"""
        if not ai_events:
            return 0
        
        # Weight different event types
        severity_weights = {
            AIDetectionType.NO_FACE_DETECTED: 1.5,
            AIDetectionType.MULTIPLE_FACES: 2.0,
            AIDetectionType.LOOKING_AWAY: 1.0,
            AIDetectionType.EXCESSIVE_HEAD_MOVEMENT: 0.8,
        }
        
        total_score = 0
        for event in ai_events:
            weight = severity_weights.get(event.detection_type, 1.0)
            total_score += event.severity * weight * event.confidence
        
        return min(100, int(total_score))
    
    def _initialize_session_state(self, session_id: str):
        """Initialize session state tracking"""
        if session_id not in self.session_states:
            self.session_states[session_id] = {
                "start_time": datetime.now(timezone.utc),
                "no_face_start_time": None,
                "last_face_time": None,
                "total_events": 0,
                "suspicious_events": 0
            }
    
    def _update_session_state(self, 
                             session_id: str, 
                             face_detection: FaceDetectionResult, 
                             ai_events: List[AIDetectionEvent]):
        """Update session state with new detection results"""
        session_state = self.session_states[session_id]
        
        # Track face detection
        if face_detection.face_count > 0:
            session_state["last_face_time"] = datetime.now(timezone.utc)
            if "no_face_start_time" in session_state:
                del session_state["no_face_start_time"]
        else:
            if "no_face_start_time" not in session_state:
                session_state["no_face_start_time"] = datetime.now(timezone.utc)
        
        # Update event counts
        session_state["total_events"] += len(ai_events)
        session_state["suspicious_events"] += len([e for e in ai_events if e.severity > 50])
    
    def _create_empty_result(self, 
                           session_id: str, 
                           student_id: str, 
                           exam_id: Optional[str],
                           frame_timestamp: datetime, 
                           start_time: datetime) -> AIDetectionResult:
        """Create empty result for skipped frames"""
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        return AIDetectionResult(
            session_id=session_id,
            student_id=student_id,
            exam_id=exam_id,
            frame_timestamp=frame_timestamp,
            face_detection=FaceDetectionResult(
                face_count=0,
                confidence=0.0,
                timestamp=frame_timestamp
            ),
            ai_events=[],
            processing_time_ms=processing_time,
            suspicious_score=0
        )
    
    def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a session"""
        if session_id not in self.session_states:
            return None
        
        session_state = self.session_states[session_id]
        duration = (datetime.now(timezone.utc) - session_state["start_time"]).total_seconds()
        
        return {
            "session_id": session_id,
            "duration_seconds": duration,
            "total_events": session_state["total_events"],
            "suspicious_events": session_state["suspicious_events"],
            "compliance_score": max(0, 100 - (session_state["suspicious_events"] * 10))
        }
    
    def cleanup_session(self, session_id: str):
        """Clean up session data"""
        if session_id in self.session_states:
            del self.session_states[session_id]
        if session_id in self.last_events:
            del self.last_events[session_id]


# Global AI detection service instance
ai_detection_service: Optional[AIDetectionService] = None


def get_ai_detection_service() -> Optional[AIDetectionService]:
    """Get the global AI detection service instance"""
    return ai_detection_service


def initialize_ai_detection(config: AIDetectionConfig) -> AIDetectionService:
    """Initialize the global AI detection service"""
    global ai_detection_service
    ai_detection_service = AIDetectionService(config)
    return ai_detection_service
