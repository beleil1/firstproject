from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Response
from db.mongo import connection
from schemas.auth_repo import authentication
import imghdr
from models.model import FileResponse
from services.minio_setup import upload_file_to_minio, download_file_from_minio
from datetime import datetime
from schemas.user_repo import convert_object_ids
bucket_name = "upload"
router = APIRouter(prefix='/user', tags=["User Api"])


@router.get('/me')
async def user_info(current_user=Depends(authentication.authenticate_token())):
    current_user.pop("password", None)
    current_user = convert_object_ids(current_user)
    return current_user


@router.post("/upload_profile_pic/", response_model=FileResponse)
async def upload_file(file: UploadFile = File(...), current_user=Depends(authentication.authenticate_token())):
    try:
        content = await file.read()
        file_type = imghdr.what(None, h=content)

        if file_type not in ["jpeg", "png"]:
            raise HTTPException(
                status_code=400, detail="Only image files are allowed (jpeg, png).")

        await file.seek(0)

        minio_url = upload_file_to_minio(
            file.file.read(),
            file.filename,
            file.content_type
        )
        download_url = f"/user/download/{file.filename}"
        upload_time = datetime.utcnow()

        user_data = connection.site_database.users.find_one_and_update(
            {"username": current_user["username"]},
            {"$set": {
                "filename": file.filename,
                "minio_url": minio_url,
                "download_url": download_url,
                "upload_time": upload_time,
            }},
            return_document=True
        )

        return FileResponse(
            filename=file.filename,
            content_type=file.content_type,
            minio_url=minio_url,
            download_url=download_url,
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while uploading the file: {str(e)}"
        )


@router.get("/download/{file_name}", response_class=Response)
async def download_file(file_name=str, current_user=Depends(authentication.authenticate_token())):
    if not file_name:
        raise HTTPException(
            status_code=400, detail="File name must be provided.")

    file_data = download_file_from_minio(bucket_name, filename=file_name)

    if file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
        media_type = "image/jpeg"
    elif file_name.lower().endswith('.png'):
        media_type = "image/png"
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported file format.")

    return Response(content=file_data, media_type=media_type)
