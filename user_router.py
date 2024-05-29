from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from mongo import connection
from utills import jwt_tools
from auth_repo import authentication
import os
import imghdr
from model import FileResponse
from minio_setup import upload_file_to_minio
from datetime import datetime


router = APIRouter(prefix='/user', tags=["User Api"])


@router.post('/me')
async def user_info(current_user=Depends(authentication.authenticate_token())):
    current_user.pop("password")
    return current_user


@router.post("/upload_profile_pic/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), current_user=Depends(authentication.authenticate_token())):
    try:
        content = await file.read()
        file_type = imghdr.what(None, h=content)
        await file.seek(0)

        if file_type not in ["jpeg", "png", "gif"]:
            raise HTTPException(
                status_code=400, detail="Only image files are allowed (jpeg, png, gif).")

        minio_url = upload_file_to_minio(
            file.file, file.filename, file.content_type)
        download_url = f"/user/download/{file.filename}"
        upload_time = datetime.utcnow()

        user_data = connection.site_database.users.find_one_and_update(
            {"username": current_user["username"]},
            {"$set": {
                "filename": file.filename,
                "minio_url": minio_url,
                "download_url": download_url,
                "upload_time": upload_time,
                "old_minio_url": minio_url,
                "old_download_url": download_url
            }},
            return_document=True
        )

        return FileResponse(filename=file.filename,
                            content_type=file.content_type,
                            minio_url=minio_url, download_url=download_url,
                            )

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while uploading the file: {str(e)}"
        )
