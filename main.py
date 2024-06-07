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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Chat Application API",
        version="1.0.0",
        description="This is a simple chat application with WebSocket support",
        routes=app.routes,
    )
    openapi_schema["paths"]["/ws/{user_id}"] = {
        "get": {
            "summary": "WebSocket endpoint for real-time chat",
            "description": """
            WebSocket endpoint for real-time chat.
            To use this endpoint, connect to `ws://yourdomain/ws/{user_id}` with a WebSocket client.
            """,
            "responses": {
                "200": {
                    "description": "Successful connection",
                },
                "400": {
                    "description": "Invalid user ID or authentication error",
                }
            }
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
