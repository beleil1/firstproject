
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.wbconnection import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{current_user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, current_user_id: str, friend_id: str):
    """
    WebSocket endpoint for real-time messaging.

    - `current_user_id`: The ID of the current user.
    - `friend_id`: The ID of the friend user.

    This WebSocket endpoint allows real-time messaging between two users.
    """
    await manager.connect_with_friends(current_user_id, friend_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            # این قسمت را بر اساس نیاز خود تغییر دهید
            sender_id = validate_object_id(current_user_id)
            receiver_id = validate_object_id(friend_id)

            message_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": message,
                # استفاده از زمان UTC برای استانداردسازی
                "timestamp": datetime.utcnow().isoformat()
            }
            # این قسمت را بر اساس نیاز خود تغییر دهید
            await connection.site_database.messages.insert_one(message_data)
            await manager.send_message_to_friend(current_user_id, friend_id, message)
    except WebSocketDisconnect:
        manager.disconnect(current_user_id, friend_id)
