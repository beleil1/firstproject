
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect_with_friends(self, current_user_id: str, friend_id: str, websocket: WebSocket):
        await websocket.accept()
        # اینجا باید مدیریت اتصال بین دو کاربر انجام شود
        # مثلاً، به فهرست کانکشن‌های فعال دوستان اضافه شود
        if current_user_id not in self.active_connections:
            self.active_connections[current_user_id] = []
        self.active_connections[current_user_id].append(websocket)

    async def send_message_to_friend(self, current_user_id: str, friend_id: str, message: str):
        # ارسال پیام به دوست
        if friend_id in self.active_connections:
            for connection in self.active_connections[friend_id]:
                await connection.send_text(message)

    def disconnect(self, current_user_id: str, friend_id: str):
        # اینجا باید اتصال بین دوستان قطع شود
        if current_user_id in self.active_connections:
            self.active_connections[current_user_id] = [
                conn for conn in self.active_connections[current_user_id] if not conn.client_state
            ]
            if not self.active_connections[current_user_id]:
                del self.active_connections[current_user_id]
