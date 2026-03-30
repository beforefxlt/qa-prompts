import boto3
import os
from io import BytesIO
from typing import Optional
from botocore.exceptions import ClientError
from pydantic_settings import BaseSettings

class StorageSettings(BaseSettings):
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "health-records")
    USE_SSL: bool = os.getenv("MINIO_USE_SSL", "False").lower() == "true"

storage_settings = StorageSettings()

class StorageClient:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"{'https' if storage_settings.USE_SSL else 'http'}://{storage_settings.MINIO_ENDPOINT}",
            aws_access_key_id=storage_settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=storage_settings.MINIO_SECRET_KEY,
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=storage_settings.MINIO_BUCKET)
        except ClientError:
            self.s3.create_bucket(Bucket=storage_settings.MINIO_BUCKET)

    def upload_file(self, content: bytes, file_name: str, content_type: str = "image/webp") -> str:
        self.s3.put_object(
            Bucket=storage_settings.MINIO_BUCKET,
            Key=file_name,
            Body=content,
            ContentType=content_type
        )
        return f"{storage_settings.MINIO_BUCKET}/{file_name}"

    def get_file(self, file_name: str) -> bytes:
        response = self.s3.get_object(Bucket=storage_settings.MINIO_BUCKET, Key=file_name)
        return response["Body"].read()

storage_client = StorageClient()
