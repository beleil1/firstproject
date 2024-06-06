from fastapi import APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, Depends
from services.wbconnection import ConnectionManager
from schemas.auth_repo import authentication
router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/friends/{current_user_id}/{friend_id}")
async def websocket_endpoint(websocket: WebSocket, friend_id: str, current_user=Depends(authentication.authenticate_token())):
    await manager.connect_with_friends(current_user_id, friend_id, websocket)
    try:
        while True:
            message = await websocket.receive_text()
            await manager.send_message_to_friend(current_user_id, friend_id, message)
    except WebSocketDisconnect:
        manager.disconnect(current_user_id, friend_id)
