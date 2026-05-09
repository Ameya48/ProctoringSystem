from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer

from app.core.deps import decode_jwt_subject
from app.models.ai_detection import (
    AIDetectionConfig,
    AIDetectionResult,
    AIAlert,
    AIAnalytics
)
from app.services.ai_detection import get_ai_detection_service, initialize_ai_detection
from app.core.ws import ai_alerts_ws_manager

router = APIRouter(prefix="/ai", tags=["ai-detection"])
security = HTTPBearer()


@router.post("/config")
async def update_ai_config(
    config: AIDetectionConfig,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Update AI detection configuration"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        # In a real implementation, you'd check if user has admin privileges
        
        service = get_ai_detection_service()
        if not service:
            service = initialize_ai_detection(config)
        else:
            # Update service config (you'd need to implement this)
            service.config = config
        
        return {"message": "AI detection configuration updated", "config": config.dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config")
async def get_ai_config(
    token: str = Depends(security)
) -> AIDetectionConfig:
    """Get current AI detection configuration"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        service = get_ai_detection_service()
        
        if not service:
            return AIDetectionConfig()
        
        return service.config
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze-frame")
async def analyze_frame(
    session_id: str,
    student_id: str,
    exam_id: Optional[str] = None,
    frame_data: bytes = b"",
    token: str = Depends(security)
) -> AIDetectionResult:
    """Analyze a single frame for AI detection"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        service = get_ai_detection_service()
        
        if not service:
            raise HTTPException(status_code=400, detail="AI detection service not initialized")
        
        if not frame_data:
            raise HTTPException(status_code=400, detail="No frame data provided")
        
        result = await service.process_frame(
            session_id=session_id,
            student_id=student_id,
            exam_id=exam_id,
            frame_data=frame_data,
            frame_timestamp=datetime.now(timezone.utc)
        )
        
        # Send real-time alerts if suspicious score is high
        if result.suspicious_score >= service.config.auto_alert_threshold:
            await _send_ai_alerts(result)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/{session_id}")
async def get_session_analytics(
    session_id: str,
    token: str = Depends(security)
) -> Dict[str, Any]:
    """Get AI analytics for a specific session"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        service = get_ai_detection_service()
        
        if not service:
            raise HTTPException(status_code=400, detail="AI detection service not initialized")
        
        analytics = service.get_session_analytics(session_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup/{session_id}")
async def cleanup_session(
    session_id: str,
    token: str = Depends(security)
) -> Dict[str, str]:
    """Clean up AI detection data for a session"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        service = get_ai_detection_service()
        
        if not service:
            raise HTTPException(status_code=400, detail="AI detection service not initialized")
        
        service.cleanup_session(session_id)
        
        return {"message": f"Session {session_id} cleaned up successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_ai_alerts(
    session_id: Optional[str] = None,
    severity_threshold: int = 0,
    limit: int = 50,
    token: str = Depends(security)
) -> List[AIAlert]:
    """Get AI alerts with optional filtering"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        # In a real implementation, you'd fetch from database
        # For now, return empty list
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    token: str = Depends(security)
) -> Dict[str, str]:
    """Acknowledge an AI alert"""
    try:
        user_id = decode_jwt_subject(token.credentials)
        # In a real implementation, you'd update the alert in database
        return {"message": f"Alert {alert_id} acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/alerts")
async def websocket_ai_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time AI alerts"""
    await websocket.accept()
    await ai_alerts_ws_manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        ai_alerts_ws_manager.disconnect(websocket)


async def _send_ai_alerts(detection_result: AIDetectionResult):
    """Send AI alerts through WebSocket"""
    try:
        for event in detection_result.ai_events:
            if event.severity >= 50:  # Only send alerts for significant events
                alert_data = {
                    "type": "ai_alert",
                    "session_id": detection_result.session_id,
                    "student_id": detection_result.student_id,
                    "exam_id": detection_result.exam_id,
                    "alert_type": event.detection_type.value,
                    "severity": event.severity,
                    "confidence": event.confidence,
                    "message": _get_alert_message(event.detection_type),
                    "details": event.details,
                    "timestamp": event.timestamp.isoformat(),
                    "suspicious_score": detection_result.suspicious_score
                }
                
                await ai_alerts_ws_manager.broadcast(alert_data)
    except Exception as e:
        print(f"Error sending AI alerts: {e}")


def _get_alert_message(detection_type) -> str:
    """Get human-readable alert message for detection type"""
    messages = {
        "no_face_detected": "No face detected in camera view",
        "multiple_faces": "Multiple faces detected in camera view",
        "looking_away": "Student looking away from screen",
        "excessive_head_movement": "Excessive head movement detected",
        "face_not_visible": "Face not clearly visible",
        "suspicious_object": "Suspicious object detected",
        "abnormal_behavior": "Abnormal behavior detected"
    }
    return messages.get(detection_type.value, "Suspicious activity detected")
