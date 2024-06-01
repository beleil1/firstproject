
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from db.mongo import connection
from schemas.auth_repo import authentication
from models.model import MessageModel
from services.minio_setup import upload_file_to_minio
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/messageu/", response_model=MessageModel)
async def create_message(sender_id: str,  # sender mishe admin recevir user ghesmt admin
                         ticket_id: str,
                         receiver_id: str,
                         message_type: str,
                         content: Optional[str] = None,
                         file: Optional[UploadFile] = None,
                         current_user=Depends(
                             authentication.authenticate_token())
                         ):
    try:
        message_data = {
            "ticket_id": ticket_id,
            "receiver_id": receiver_id,
            "message_type": message_type,
            "upload_time": datetime.utcnow()
        }
        # if message_type not in ["text", "image", "video", "file"]:

        #     raise HTTPException(
        #         status_code=400, detail="Invalid message type.")

        if message_type == "text":
            if not content:
                raise HTTPException(
                    status_code=400, detail="Content is required for text messages.")
            message_data["content"] = content
        # else:
        #     # if file is None:
        #     raise HTTPException(
        #         status_code=400, detail="File is required for this message type.")

            minio_url = upload_file_to_minio(
                file.file, file.filename, file.content_type)
            message_data.update({
                "filename": file.filename,
                "minio_url": minio_url,
                "content": content
            })
        connection.site_database.messages.insert_one(message_data)
        return message_data

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while sending the message: {str(e)}"
        )
