from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from fastapi import APIRouter, HTTPException, status, Depends
from mongo import connection
from utills import jwt_tools
from auth_repo import authentication
import os
from model import FileResponse
from minio_setup import upload_file_to_minio
from mongo import connection

router = APIRouter(prefix='/user', tags=["User Api"])


@router.post('/me')
async def user_info(current_user=Depends
                    (authentication.authenticate_token())):

    current_user.pop("password")
    return current_user


router = APIRouter(prefix='/user', tags=["User Api"])


@router.post('/me')
async def user_info(current_user=Depends(authentication.authenticate_token())):
    current_user.pop("password")
    return current_user


@router.post("/uploadfile/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), current_user=Depends(authentication.authenticate_token())):
    try:
        minio_url = upload_file_to_minio(
            file.file, file.filename, file.content_type)
        download_url = f"/user/download/{file.filename}"

        connection.site_database.users.update_one(
            {"username": current_user["username"]},
            {"$set": {
                "filename": file.filename,
                "minio_url": minio_url,
                "download_url": download_url
            }})

        return FileResponse(filename=file.filename, content_type=file.content_type, minio_url=minio_url, download_url=download_url)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An error occurred while uploading the file: {str(e)}")
