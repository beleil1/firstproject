from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.wbconnection import ConnectionManager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{current_user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, current_user_id: str, friend_id: str):
    await manager.connect_with_friends(current_user_id, friend_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            sender_id = current_user_id
            receiver_id = friend_id

            message_data = {
                "sender_id": sender_id,
                "receiver_id": receiver_id,
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            await connection.site_database.messages.insert_one(message_data)
            await manager.send_message_to_friend(current_user_id, friend_id, message)
    except WebSocketDisconnect:
        manager.disconnect(current_user_id, friend_id)
