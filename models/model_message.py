from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from bson import ObjectId


class FriendRequest(BaseModel):
    from_user: str
    to_user: str


class FriendAccept(BaseModel):
    from_user: str
    to_user: str
    status: str = "pending"


class Message(BaseModel):
    sender_id: str
    receiver_id: str
    content: str
    timestamp: str
