# websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from services.wbconnection import ConnectionManager
from db.mongo import connection
from datetime import datetime
from bson import ObjectId, errors

router = APIRouter()
manager = ConnectionManager()


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

            # ذخیره پیام در پایگاه داده
            message_data = {
                "sender_id": validate_object_id(user_id),
                "receiver_id": validate_object_id(friend_id),
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            await connection.site_database.messages.insert_one(message_data)

            # ارسال پیام به هر دو طرف چت
            await manager.send_message_to_group([user_id, friend_id], f"{user_id}: {message}")
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
