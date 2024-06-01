from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageCreate(BaseModel):
    content: str


class Message(BaseModel):
    id: str
    content: str
    timestamp: datetime


class TicketCreate(BaseModel):
    subject: str
    messages: List[MessageCreate]


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    messages: Optional[List[MessageCreate]] = None


class Ticket(BaseModel):
    id: str
    subject: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    status: str
