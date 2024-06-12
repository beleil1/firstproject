from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from models.model_message import Message
from db.mongo import connection
from schemas.auth_repo import authentication
from bson import ObjectId, errors, json_util
from datetime import datetime
from typing import List, Dict, Tuple
from services.wbconnection import ConnectionManager

router = APIRouter(prefix='/messages', tags=["Messages API"])
manager = ConnectionManager()

messages_dict: Dict[Tuple[ObjectId, ObjectId], List[Dict[str, str]]] = {}


def validate_object_id(id: str):
    try:
        return ObjectId(id)
    except errors.InvalidId:
        raise HTTPException(
            status_code=400, detail=f"{id} is not a valid ObjectId")


async def get_username_by_id(user_id: ObjectId) -> str:
    user = await connection.site_database.users.find_one({"_id": user_id})
    if user:
        return user["username"]
    else:
        return "Unknown"


@router.post('/', description="Create and send a new message.")
async def create_message(message: Message, current_user=Depends(authentication.authenticate_token())):
    receiver_id = validate_object_id(message.receiver_id)
    sender_id = validate_object_id(current_user['id'])

    message_data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": message.content,
        "timestamp": datetime.utcnow().isoformat()
    }

    conversation = await connection.site_database.messages.find_one({
        "participants": {"$all": [sender_id, receiver_id]}
    })

    if not conversation:
        conversation = {
            "participants": [sender_id, receiver_id],
            "messages": []
        }

    conversation["messages"].append(message_data)

    await connection.site_database.messages.replace_one(
        {"participants": {"$all": [sender_id, receiver_id]}},
        conversation,
        upsert=True
    )

    return {"message": "Message sent successfully"}


@router.get('/{friend_id}', description="Retrieve messages exchanged with a friend.")
async def get_messages(friend_id: str, current_user=Depends(authentication.authenticate_token())):
    user_id = validate_object_id(current_user['id'])
    friend_id = validate_object_id(friend_id)

    messages = messages_dict.get(
        (user_id, friend_id), []) + messages_dict.get((friend_id, user_id), [])

    if not messages:
        raise HTTPException(status_code=404, detail="No messages found")

    messages_json = []
    for msg in messages:
        sender_id = msg["sender_id"]
        receiver_id = msg["receiver_id"]

        sender_username = await get_username_by_id(sender_id)
        receiver_username = await get_username_by_id(receiver_id)

        messages_json.append({
            "sender_username": sender_username,
            "receiver_username": receiver_username,
            "content": msg["content"],
            "timestamp": msg["timestamp"]
        })

    return messages_json
