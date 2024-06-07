from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from api.auth_router import router as auth_router
from api.user_router import router as user_router
from api.friendship import router as friendship_router
from services.wbconnection import ConnectionManager
from fastapi.openapi.utils import get_openapi
from api.websocket import router as websocket_router
from api.message import router as message

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(friendship_router)
app.include_router(websocket_router)
app.include_router(message)
