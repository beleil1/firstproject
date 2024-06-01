from fastapi import FastAPI
from api.auth_router import router as auth_router
from api.user_router import router as user_router
from api.message_router import router as message_router


app = FastAPI()
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(message_router)
