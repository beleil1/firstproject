from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from services.wbconnection import ConnectionManager
from db.mongo import connection
from datetime import datetime
from bson import ObjectId, errors
import json

router = APIRouter()
manager = ConnectionManager()


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


def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except errors.InvalidId:
        raise HTTPException(
            status_code=400, detail=f"{id} is not a valid ObjectId")


@router.websocket("/ws/{user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, friend_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()

            message_data = {
                "sender_id": validate_object_id(user_id),
                "receiver_id": validate_object_id(friend_id),
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            conversation = await connection.site_database.messages.find_one({
                "participants": {"$all": [message_data["sender_id"], message_data["receiver_id"]]}
            })

            if not conversation:
                conversation = {
                    "participants": [message_data["sender_id"], message_data["receiver_id"]],
                    "messages": []
                }
            conversation["messages"].append({
                "content": message_data["content"],
                "timestamp": message_data["timestamp"],
                "sender_id": message_data["sender_id"]
            })

            await connection.site_database.messages.replace_one(
                {"participants": {
                    "$all": [message_data["sender_id"], message_data["receiver_id"]]}},
                conversation,
                upsert=True
            )

            sender_user = await connection.site_database.users.find_one({"_id": ObjectId(user_id)}, {"username": 1})
            if not sender_user:
                sender_username = "Unknown User"
            else:
                sender_username = sender_user.get("username", "Unknown User")

            formatted_message = {
                "sender_id": user_id,
                "sender_username": sender_username,
                "content": message,
                "timestamp": message_data["timestamp"]
            }
            await manager.send_message_to_user(friend_id, json.dumps(formatted_message))
    except WebSocketDisconnect:
        manager.disconnect(user_id)
