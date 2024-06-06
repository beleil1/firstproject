from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from models.model_message import Message
from db.mongo import connection
from schemas.auth_repo import authentication
from bson import ObjectId
from datetime import datetime
from typing import List
from services.wbconnection import ConnectionManager
from models.model_message import Message

router = APIRouter(prefix='/messages', tags=["Messages API"])
manager = ConnectionManager()


@router.post('/')
async def create_message(message: Message, current_user=Depends(authentication.authenticate_token())):
    message_data = {
        "sender_id": ObjectId(message.sender_id),
        "receiver_id": ObjectId(message.receiver_id),
        "content": message.content,
        "timestamp": datetime.now().isoformat()
    }
    result = await connection.site_database.messages.insert_one(message_data)
    if result.inserted_id:
        return {"message": "Message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get('/{friend_id}')
async def get_messages(friend_id: str, current_user=Depends(authentication.authenticate_token())):
    user_id = ObjectId(current_user['id'])
    friend_id = ObjectId(friend_id)

    messages = await connection.site_database.messages.find({
        "$or": [
            {"sender_id": user_id, "receiver_id": friend_id},
            {"sender_id": friend_id, "receiver_id": user_id}
        ]
    }).to_list(length=100)

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    return messages


@router.websocket("/ws/{current_user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, current_user_id: str, friend_id: str):
    await manager.connect_with_friends(current_user_id, friend_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            message_data = {
                "sender_id": ObjectId(current_user_id),
                "receiver_id": ObjectId(friend_id),
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            await connection.site_database.messages.insert_one(message_data)
            await manager.send_message_to_friend(current_user_id, friend_id, message)
    except WebSocketDisconnect:
        manager.disconnect(current_user_id, friend_id)
