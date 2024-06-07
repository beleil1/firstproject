from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from models.model_message import Message
from db.mongo import connection
from schemas.auth_repo import authentication
from bson import ObjectId, errors, json_util
from datetime import datetime
from typing import List
from services.wbconnection import ConnectionManager

router = APIRouter(prefix='/messages', tags=["Messages API"])
manager = ConnectionManager()


def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except errors.InvalidId:
        raise HTTPException(
            status_code=400, detail=f"{id} is not a valid ObjectId")


@router.post('/', description="Create and send a new message.")
async def create_message(message: Message, current_user=Depends(authentication.authenticate_token())):
    receiver_id = validate_object_id(message.receiver_id)

    message_data = {
        # استخراج و اعتبارسنجی ID کاربر جاری
        "sender_id": validate_object_id(current_user['id']),
        "receiver_id": receiver_id,
        "content": message.content,
        # استفاده از زمان UTC برای استانداردسازی
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await connection.site_database.messages.insert_one(message_data)
    if result.inserted_id:
        return {"message": "Message sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.get('/{friend_id}', description="Retrieve messages exchanged with a friend.")
async def get_messages(friend_id: str, current_user=Depends(authentication.authenticate_token())):
    user_id = validate_object_id(current_user['id'])
    friend_id = validate_object_id(friend_id)

    messages = await connection.site_database.messages.find({
        "$or": [
            {"sender_id": user_id, "receiver_id": friend_id},
            {"sender_id": friend_id, "receiver_id": user_id}
        ]
    }).to_list(length=100)

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    messages_json = [{"sender_id": str(msg["sender_id"]),
                      "receiver_id": str(msg["receiver_id"]),
                      "content": msg["content"],
                      "timestamp": msg["timestamp"]} for msg in messages]

    return messages_json
