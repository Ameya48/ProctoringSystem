from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.deps import decode_jwt_subject
from app.core.ws import events_ws_manager, sessions_ws_manager
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.routes.auth import router as auth_router
from app.routes.events import router as events_router
from app.routes.health import router as health_router
from app.routes.recordings import router as recordings_router
from app.routes.sessions import router as sessions_router
from app.routes.webcam import router as webcam_router

# AI detection temporarily disabled for demo
# from app.models.ai_detection import AIDetectionConfig
# from app.routes.ai_detection import router as ai_detection_router
# from app.services.ai_detection import initialize_ai_detection, get_ai_detection_service

app = FastAPI(title="Online Proctoring System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    await connect_to_mongo()
    # AI detection service temporarily disabled
    # ai_config = AIDetectionConfig()
    # initialize_ai_detection(ai_config)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_mongo_connection()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(events_router)
app.include_router(webcam_router)
app.include_router(recordings_router)
# AI detection router temporarily disabled
# app.include_router(ai_detection_router)

# Serve stored media (webcam screenshots, etc.)
_storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
os.makedirs(_storage_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=_storage_dir), name="media")


@app.websocket("/ws/sessions")
async def ws_sessions(websocket: WebSocket):
    await sessions_ws_manager.connect(websocket)
    try:
        # keep the connection alive; clients may optionally send pings
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        sessions_ws_manager.disconnect(websocket)
    except Exception:
        sessions_ws_manager.disconnect(websocket)


@app.websocket("/ws/webcam")
async def ws_webcam(
    websocket: WebSocket,
    token: str = Query(...),
    session_id: str = Query(...),
    exam_id: str = Query(None),
):
    """
    Receives binary JPEG frames from the browser and periodically saves screenshots + logs metadata.
    Auth: JWT passed as query param `token` (typical for browser WebSockets).
    """
    await websocket.accept()

    # authenticate
    user_id = decode_jwt_subject(token)

    db = None
    try:
        from app.db.mongo import get_db

        db = get_db()
    except Exception:
        # if DB isn't ready, fail fast
        await websocket.close(code=1011)
        return

    # validate active session belongs to this student
    session = await db["sessions"].find_one({"_id": session_id})
    if not session or session.get("student_id") != user_id:
        await websocket.close(code=1008)  # policy violation
        return

    # directory to save screenshots
    base_dir = os.path.join(os.path.dirname(__file__), "..", "storage", "webcam", session_id)
    base_dir = os.path.abspath(base_dir)
    os.makedirs(base_dir, exist_ok=True)

    # low-latency: accept frames fast, save periodically (server-controlled)
    save_every_seconds = 10
    last_saved_at = datetime.fromtimestamp(0, tz=timezone.utc)
    frames_received = 0

    try:
        while True:
            message = await websocket.receive()

            # ignore text pings/control
            if message.get("text") is not None:
                continue

            data = message.get("bytes")
            if not data:
                continue

            frames_received += 1
            now = datetime.now(timezone.utc)

            # AI Detection temporarily disabled for demo
            # ai_service = get_ai_detection_service()
            # if ai_service:
            #     try:
            #         ai_result = await ai_service.process_frame(
            #             session_id=session_id,
            #             student_id=user_id,
            #             exam_id=exam_id,
            #             frame_data=data,
            #             frame_timestamp=now
            #         )
            #         
            #         # Store AI detection results in database
            #         if ai_result.ai_events:
            #             ai_doc = ai_result.dict()
            #             await db["ai_detections"].insert_one(ai_doc)
            #         
            #         # Broadcast AI alerts if suspicious
            #         if ai_result.suspicious_score >= 70:
            #             await ai_alerts_ws_manager.broadcast({
            #                 "type": "ai_alert",
            #                 "session_id": session_id,
            #                 "student_id": user_id,
            #                 "exam_id": exam_id,
            #                 "suspicious_score": ai_result.suspicious_score,
            #                 "events": [event.dict() for event in ai_result.ai_events],
            #                 "timestamp": now.isoformat()
            #             })
            #     except Exception as e:
            #         # Log error but don't interrupt stream
            #         print(f"AI detection error: {e}")

            should_save = (now - last_saved_at).total_seconds() >= save_every_seconds
            if not should_save:
                continue

            last_saved_at = now
            ts = now.strftime("%Y%m%dT%H%M%S%fZ")
            filename = f"{ts}.jpg"
            path = os.path.join(base_dir, filename)

            try:
                with open(path, "wb") as f:
                    f.write(data)
            except Exception:
                await websocket.send_json({"type": "error", "message": "Failed to save screenshot"})
                continue

            doc = {
                "session_id": session_id,
                "student_id": user_id,
                "exam_id": exam_id,
                "captured_at": now,
                "saved_path": path,
                "content_type": "image/jpeg",
                "size_bytes": len(data),
                "frames_received": frames_received,
            }
            try:
                await db["webcam_logs"].insert_one(doc)
            except Exception:
                # don't kill stream if logging fails
                pass

            # acknowledge saved screenshot (helps client show status)
            await websocket.send_json({"type": "saved", "captured_at": now.isoformat(), "size_bytes": len(data)})
            # notify proctor dashboards (best-effort)
            try:
                rel = os.path.relpath(path, _storage_dir)
                await events_ws_manager.broadcast(
                    {
                        "type": "webcam_saved",
                        "webcam": {
                            "session_id": session_id,
                            "student_id": user_id,
                            "exam_id": exam_id,
                            "captured_at": now.isoformat(),
                            "media_url": f"/media/{rel.replace(os.sep, '/')}",
                            "size_bytes": len(data),
                        },
                    }
                )
            except Exception:
                pass

    except WebSocketDisconnect:
        return
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


def _score_event(event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Alert generation logic:
    - Returns {suspicious: bool, severity: int}
    """
    severity_map = {
        "fullscreen_exited": 90,
        "tab_hidden": 80,
        "window_blur": 70,
        "idle": 60,
        "screen_share_stopped": 75,
    }
    base = int(severity_map.get(event_type, 10))
    if details.get("duration_ms"):
        try:
            dur = int(details["duration_ms"])
            base = min(100, base + (10 if dur > 10_000 else 0))
        except Exception:
            pass
    suspicious = base >= 60
    return {"suspicious": suspicious, "severity": base}


@app.websocket("/ws/events")
async def ws_events(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    Student clients: send JSON events to ingest.
    Proctor clients: receive broadcasts (and may also receive their own connection ack).
    """
    user_id = decode_jwt_subject(token)
    from app.db.mongo import get_db

    db = get_db()
    user = await db["users"].find_one({"_id": user_id})
    if not user:
        await websocket.close(code=1008)
        return

    role = user.get("role")
    # Everyone can subscribe; only students can ingest.
    await events_ws_manager.connect(websocket)
    await websocket.send_json({"type": "connected", "role": role})

    try:
        while True:
            msg = await websocket.receive_json()
            if role != "student":
                # proctors shouldn't ingest events
                continue

            event_type = str(msg.get("event_type") or "")
            session_id = str(msg.get("session_id") or "")
            exam_id = msg.get("exam_id")
            details = msg.get("details") or {}
            ts_raw = msg.get("timestamp")

            if not event_type or not session_id:
                continue

            session = await db["sessions"].find_one({"_id": session_id})
            if not session or session.get("student_id") != user_id:
                continue

            # parse timestamp (optional)
            timestamp = datetime.now(timezone.utc)
            if isinstance(ts_raw, str):
                try:
                    timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                except Exception:
                    pass

            score = _score_event(event_type, details)
            doc = {
                "session_id": session_id,
                "student_id": user_id,
                "exam_id": exam_id,
                "event_type": event_type,
                "timestamp": timestamp,
                "details": details,
                **score,
            }

            try:
                await db["proctoring_events"].insert_one(doc)
            except Exception:
                # still broadcast even if insert fails (best effort)
                pass

            # broadcast to all connected proctor dashboards + students
            await events_ws_manager.broadcast({"type": "event", "event": doc})
            if doc["suspicious"]:
                await events_ws_manager.broadcast({"type": "alert", "event": doc})

    except WebSocketDisconnect:
        events_ws_manager.disconnect(websocket)
    except Exception:
        events_ws_manager.disconnect(websocket)

