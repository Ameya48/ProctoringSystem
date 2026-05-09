from __future__ import annotations

import json
from typing import Any, Dict, List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        data = json.dumps(message, default=str)
        to_remove: List[WebSocket] = []
        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                to_remove.append(ws)
        for ws in to_remove:
            self.disconnect(ws)


sessions_ws_manager = ConnectionManager()

# Used for real-time proctoring event updates
events_ws_manager = ConnectionManager()

# Used for real-time AI detection alerts
ai_alerts_ws_manager = ConnectionManager()

