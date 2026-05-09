from __future__ import annotations

import asyncio
import base64
from datetime import datetime, timezone
from typing import Any, Dict

from celery import current_app
from app.celery_app import celery_app
from app.services.ai_detection import get_ai_detection_service
from app.db.mongo import get_db
from app.core.logging import ai_logger
import structlog

logger = structlog.get_logger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_ai_detection_async(
    self,
    session_id: str,
    student_id: str,
    exam_id: str,
    frame_data_b64: str,
    frame_timestamp: str,
) -> Dict[str, Any]:
    """Process AI detection asynchronously"""
    try:
        # Decode frame data
        frame_data = base64.b64decode(frame_data_b64)
        timestamp = datetime.fromisoformat(frame_timestamp.replace('Z', '+00:00'))
        
        # Get AI service
        ai_service = get_ai_detection_service()
        if not ai_service:
            raise Exception("AI detection service not available")
        
        # Process frame in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                ai_service.process_frame(
                    session_id=session_id,
                    student_id=student_id,
                    exam_id=exam_id,
                    frame_data=frame_data,
                    frame_timestamp=timestamp,
                )
            )
            
            # Store results in database
            db = get_db()
            if result.ai_events:
                result_dict = result.dict()
                loop.run_until_complete(
                    db["ai_detections"].insert_one(result_dict)
                )
                
                # Log suspicious activity
                for event in result.ai_events:
                    ai_logger.log_suspicious_activity(
                        session_id=session_id,
                        student_id=student_id,
                        detection_type=event.detection_type.value,
                        severity=event.severity,
                        confidence=event.confidence,
                        details=event.details,
                    )
            
            return {
                "success": True,
                "session_id": session_id,
                "student_id": student_id,
                "processing_time_ms": result.processing_time_ms,
                "face_count": result.face_detection.face_count,
                "events_detected": len(result.ai_events),
                "suspicious_score": result.suspicious_score,
            }
            
        finally:
            loop.close()
            
    except Exception as exc:
        logger.error(f"AI processing task failed: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            "success": False,
            "error": str(exc),
            "session_id": session_id,
            "student_id": student_id,
        }


@celery_app.task
def batch_process_ai_detections(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Batch process AI detections for a session"""
    try:
        session_id = session_data["session_id"]
        student_id = session_data["student_id"]
        exam_id = session_data.get("exam_id")
        
        logger.info(f"Starting batch AI processing for session {session_id}")
        
        # Get AI service
        ai_service = get_ai_detection_service()
        if not ai_service:
            raise Exception("AI detection service not available")
        
        # Get recent frames from database
        db = get_db()
        cursor = db["webcam_logs"].find(
            {"session_id": session_id},
            sort=[("captured_at", -1)],
            limit=50  # Process last 50 frames
        )
        
        frames_processed = 0
        total_events = 0
        suspicious_scores = []
        
        for frame_doc in cursor:
            try:
                # Read frame file
                import os
                if os.path.exists(frame_doc["saved_path"]):
                    with open(frame_doc["saved_path"], "rb") as f:
                        frame_data = f.read()
                    
                    # Process frame
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        result = loop.run_until_complete(
                            ai_service.process_frame(
                                session_id=session_id,
                                student_id=student_id,
                                exam_id=exam_id,
                                frame_data=frame_data,
                                frame_timestamp=frame_doc["captured_at"],
                            )
                        )
                        
                        # Store result
                        if result.ai_events:
                            result_dict = result.dict()
                            loop.run_until_complete(
                                db["ai_detections"].insert_one(result_dict)
                            )
                        
                        frames_processed += 1
                        total_events += len(result.ai_events)
                        suspicious_scores.append(result.suspicious_score)
                        
                    finally:
                        loop.close()
                        
            except Exception as e:
                logger.error(f"Error processing frame {frame_doc['_id']}: {e}")
                continue
        
        # Calculate session analytics
        avg_suspicious_score = sum(suspicious_scores) / len(suspicious_scores) if suspicious_scores else 0
        max_suspicious_score = max(suspicious_scores) if suspicious_scores else 0
        
        # Update session with analytics
        session_analytics = {
            "ai_frames_processed": frames_processed,
            "ai_events_detected": total_events,
            "ai_avg_suspicious_score": avg_suspicious_score,
            "ai_max_suspicious_score": max_suspicious_score,
            "ai_last_processed": datetime.now(timezone.utc),
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(
                db["sessions"].update_one(
                    {"_id": session_id},
                    {"$set": session_analytics}
                )
            )
        finally:
            loop.close()
        
        return {
            "success": True,
            "session_id": session_id,
            "frames_processed": frames_processed,
            "total_events": total_events,
            "avg_suspicious_score": avg_suspicious_score,
            "max_suspicious_score": max_suspicious_score,
        }
        
    except Exception as exc:
        logger.error(f"Batch AI processing failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "session_id": session_data.get("session_id"),
        }


@celery_app.task
def generate_ai_alert(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate and send AI alert"""
    try:
        session_id = alert_data["session_id"]
        student_id = alert_data["student_id"]
        detection_type = alert_data["detection_type"]
        severity = alert_data["severity"]
        confidence = alert_data["confidence"]
        details = alert_data["details"]
        
        logger.warning(
            f"AI alert generated for session {session_id}",
            detection_type=detection_type,
            severity=severity,
            confidence=confidence,
        )
        
        # Store alert in database
        db = get_db()
        alert_doc = {
            "session_id": session_id,
            "student_id": student_id,
            "alert_type": detection_type,
            "severity": severity,
            "confidence": confidence,
            "details": details,
            "timestamp": datetime.now(timezone.utc),
            "acknowledged": False,
            "resolved": False,
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                db["ai_alerts"].insert_one(alert_doc)
            )
            
            # Send real-time notification via WebSocket
            from app.core.ws import ai_alerts_ws_manager
            
            alert_notification = {
                "type": "ai_alert",
                "alert_id": str(result.inserted_id),
                "session_id": session_id,
                "student_id": student_id,
                "alert_type": detection_type,
                "severity": severity,
                "confidence": confidence,
                "message": get_alert_message(detection_type),
                "details": details,
                "timestamp": alert_doc["timestamp"].isoformat(),
            }
            
            # Run async WebSocket broadcast in event loop
            loop.run_until_complete(ai_alerts_ws_manager.broadcast(alert_notification))
            
        finally:
            loop.close()
        
        return {
            "success": True,
            "alert_id": str(result.inserted_id),
            "session_id": session_id,
            "detection_type": detection_type,
        }
        
    except Exception as exc:
        logger.error(f"AI alert generation failed: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "session_id": alert_data.get("session_id"),
        }


def get_alert_message(detection_type: str) -> str:
    """Get human-readable alert message"""
    messages = {
        "no_face_detected": "No face detected in camera view",
        "multiple_faces": "Multiple faces detected in camera view",
        "looking_away": "Student looking away from screen",
        "excessive_head_movement": "Excessive head movement detected",
        "face_not_visible": "Face not clearly visible",
        "suspicious_object": "Suspicious object detected",
        "abnormal_behavior": "Abnormal behavior detected",
    }
    return messages.get(detection_type, "Suspicious activity detected")
