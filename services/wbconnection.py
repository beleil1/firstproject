# services/wbconnection.py

from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected")

    async def send_message_to_user(self, user_id: str, message: str):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_text(message)
        else:
            print(f"User {user_id} not connected")

    async def send_message_to_all(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)
