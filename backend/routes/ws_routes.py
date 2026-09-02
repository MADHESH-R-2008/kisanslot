from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class ConnectionManager:
    def __init__(self):
        # Maps centre_id -> list of active websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, centre_id: int):
        await websocket.accept()
        if centre_id not in self.active_connections:
            self.active_connections[centre_id] = []
        self.active_connections[centre_id].append(websocket)
        logger.info(f"Client connected to centre {centre_id}. Total: {len(self.active_connections[centre_id])}")

    def disconnect(self, websocket: WebSocket, centre_id: int):
        if centre_id in self.active_connections:
            if websocket in self.active_connections[centre_id]:
                self.active_connections[centre_id].remove(websocket)
            if not self.active_connections[centre_id]:
                del self.active_connections[centre_id]

    async def broadcast(self, message: dict, centre_id: int):
        """Broadcasts a JSON message to all clients connected to a specific centre queue."""
        if centre_id in self.active_connections:
            json_msg = json.dumps(message)
            for connection in self.active_connections[centre_id]:
                try:
                    await connection.send_text(json_msg)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

@router.websocket("/queue/{centre_id}")
async def websocket_queue_endpoint(websocket: WebSocket, centre_id: int):
    """
    WebSocket endpoint for real-time queue updates.
    Both Farmer App and Admin Dashboard connect here to receive live updates.
    """
    await manager.connect(websocket, centre_id)
    try:
        while True:
            # We don't expect much data from clients, just ping/pong or keep-alive
            data = await websocket.receive_text()
            # Respond with ack if they send something
            await websocket.send_text(json.dumps({"event": "ACK", "message": data}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, centre_id)
        logger.info(f"Client disconnected from centre {centre_id}")
