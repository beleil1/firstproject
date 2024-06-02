from fastapi import APIRouter, HTTPException, Depends, Form, File, UploadFile
from datetime import datetime
from pydantic import BaseModel
from models.model_message import Message, Ticket, TicketCreate, MessageCreate
from schemas.auth_repo import authentication
from db.mongo import connection
from bson import ObjectId
from services.minio_setup import minio_client, upload_file_to_minio
import json
from typing import List
import secrets
from services.pyclamd import scan_file_for_virus
from bson.errors import InvalidId
router = APIRouter(prefix='/ticket', tags=["user_Admin"])


@router.post("/tickets/", response_model=Ticket)
async def create_ticket(
    subject: str = Form(...),
    messages: List[str] = Form(...),
    file: UploadFile = File(None),
    current_user=Depends(authentication.authenticate_token())
):
    ticket_dict = {
        "subject": subject,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status": "pending",
        "messages": []
    }

    if file:
        file_type = file.filename.split(".")[-1].lower()
        if file_type not in ["jpeg", "jpg", "png", "pdf"]:
            raise HTTPException(
                status_code=400, detail="Only image files (jpeg, jpg, png) and PDF files are allowed.")

        if file is not None:
            file_content = await file.read()
        if file:
            file_content = await file.read()
        if scan_file_for_virus(file_content):
            raise HTTPException(
                status_code=400, detail="Uploaded file contains a virus.")

        filename = f"{secrets.token_hex(16)}-{file.filename}"
        file_url = upload_file_to_minio(
            file_content, filename, file.content_type)
        ticket_dict["file_url"] = file_url

    for content in messages:
        ticket_dict["messages"].append(
            {"_id": ObjectId(), "content": content, "timestamp": datetime.utcnow()})

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
    try:
        object_id = ObjectId(ticket_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ticket ID")

    updated_ticket = await connection.site_database.tickets.find_one_and_update(
        {"_id": object_id},
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
    try:
        object_id = ObjectId(ticket_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ticket ID")

    new_message = {"_id": ObjectId(), "content": content,
                   "timestamp": datetime.utcnow()}

    if file:
        file_content = await file.read()
        new_message["file_name"] = file.filename
        new_message["file_content"] = file_content

    updated_ticket = await connection.site_database.tickets.find_one_and_update(
        {"_id": object_id},
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
