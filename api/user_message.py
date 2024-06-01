from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from datetime import datetime
from pydantic import BaseModel
from models.model_message import Message, Ticket, TicketCreate, MessageCreate
from schemas.auth_repo import authentication
from db.mongo import connection
from bson import ObjectId
from services.minio_setup import minio_client, upload_file_to_minio
router = APIRouter(prefix='/ticket', tags=["user_Admin"])


@router.post("/tickets/", response_model=Ticket)
async def create_ticket(ticket: TicketCreate, current_user=Depends(authentication.authenticate_token())):
    ticket_dict = ticket.dict()
    ticket_dict["created_at"] = datetime.utcnow()
    ticket_dict["updated_at"] = datetime.utcnow()
    ticket_dict["status"] = "pending"

    ticket_dict["messages"] = [
        {"_id": ObjectId(), "content": msg.content, "timestamp": datetime.utcnow()}
        for msg in ticket.messages
    ]

    new_ticket = await connection.site_database.tickets.insert_one(ticket_dict)
    created_ticket = await connection.site_database.tickets.find_one({"_id": new_ticket.inserted_id})

    if created_ticket:
        created_ticket["id"] = str(created_ticket["_id"])
        created_ticket["messages"] = [
            {"id": str(message["_id"]), "content": message["content"],
             "timestamp": message["timestamp"]}
            for message in created_ticket["messages"]
        ]
        return Ticket(**created_ticket)
    else:
        raise HTTPException(status_code=404, detail="Ticket not found")


@router.patch("/tickets/{ticket_id}/accept", response_model=Ticket)
async def accept_ticket(ticket_id: str, current_user=Depends(authentication.authenticate_token())):
    updated_ticket = await connection.site_database.tickets.find_one_and_update(
        {"_id": ObjectId(ticket_id)},
        {"$set": {"status": "accepted", "updated_at": datetime.utcnow()}},
        return_document=True
    )

    if updated_ticket:
        updated_ticket["id"] = str(updated_ticket["_id"])
        updated_ticket["messages"] = [
            {"id": str(message["_id"]), "content": message["content"],
             "timestamp": message["timestamp"]}
            for message in updated_ticket["messages"]
        ]
        return Ticket(**updated_ticket)
    else:
        raise HTTPException(status_code=404, detail="Ticket not found")


@router.post("/tickets/{ticket_id}/response", response_model=Ticket)
async def respond_to_ticket(
    ticket_id: str,
    content: str = Form(...),
    file: UploadFile = File(None), current_user=Depends(authentication.authenticate_token())

):
    new_message = {"_id": ObjectId(), "content": content,
                   "timestamp": datetime.utcnow()}

    if file:
        file_content = await file.read()
        # شما می‌توانید فایل را در پایگاه‌داده ذخیره کنید یا در دیسک ذخیره کنید و مسیر آن را در new_message قرار دهید
        # این قسمت را بر اساس نیاز خود تغییر دهید
        new_message["file_name"] = file.filename
        # در اینجا به عنوان مثال، محتوای فایل را در پیام ذخیره می‌کنیم
        new_message["file_content"] = file_content

    updated_ticket = await connection.site_database.tickets.find_one_and_update(
        {"_id": ObjectId(ticket_id)},
        {"$push": {"messages": new_message}, "$set": {
            "updated_at": datetime.utcnow()}},
        return_document=True
    )

    if updated_ticket:
        updated_ticket["id"] = str(updated_ticket["_id"])
        updated_ticket["messages"] = [
            {"id": str(msg["_id"]), "content": msg["content"],
             "timestamp": msg["timestamp"], "file_name": msg.get("file_name")}
            for msg in updated_ticket["messages"]
        ]
        return Ticket(**updated_ticket)
    else:
        raise HTTPException(status_code=404, detail="Ticket not found")
