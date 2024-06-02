from minio import Minio
from minio.error import S3Error
import secrets
import io
MINIO_ENDPOINT = "192.168.1.3:9000"
MINIO_ACCESS_KEY = "fgFZEj6rF3Wd0l1N0vh7"
MINIO_SECRET_KEY = "r48Fl7WJDT67sJeYbe3YrOkVre8QB1BUbWP2Qikk"
MINIO_BUCKET_NAME = "upload"

minio_client = Minio(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)


def upload_file_to_minio(file_data, filename, content_type):
    try:
        file_data = io.BytesIO(file_data)  # تبدیل bytes به io.BytesIO
        file_stat = file_data.getbuffer().nbytes
        minio_client.put_object(
            bucket_name=MINIO_BUCKET_NAME,
            object_name=filename,
            data=file_data,
            length=-1,
            part_size=10*1024*1024,
            content_type=content_type
        )
        minio_url = f"{MINIO_ENDPOINT}/{MINIO_BUCKET_NAME}/{filename}"
        return minio_url
    except S3Error as e:
        raise Exception(
            f"An error occurred while uploading the file: {str(e)}")
