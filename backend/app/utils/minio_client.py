"""
MinIO S3-compatible object storage client for file uploads.

Usage:
  - Profile pictures: upload_file(file_content, "profiles/user_id.jpg")
  - Assignment files: upload_file(file_content, "assignments/submission_id/filename")
  - Get download URL: url = get_presigned_download_url("profiles/user_id.jpg")
"""
import logging
from datetime import timedelta
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from app.config import settings

logger = logging.getLogger(__name__)

# Initialize MinIO client
client = Minio(
    settings.MINIO_URL.replace("http://", "").replace("https://", ""),
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_URL.startswith("https"),
)


def ensure_bucket_exists():
    """Create bucket if it doesn't exist."""
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
            logger.info("Created MinIO bucket: %s", settings.MINIO_BUCKET)
    except S3Error as e:
        logger.error("MinIO bucket creation error: %s", e)


def upload_file(file_content: bytes, object_name: str) -> str:
    """
    Upload a file to MinIO and return the object path.

    Args:
        file_content: File bytes
        object_name: Path in bucket (e.g., "profiles/user_123.jpg")

    Returns:
        Object name (path in bucket)

    Raises:
        S3Error: If upload fails
    """
    try:
        ensure_bucket_exists()
        file_obj = BytesIO(file_content)
        client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            file_obj,
            length=len(file_content),
        )
        logger.info("Uploaded file: %s", object_name)
        return object_name
    except S3Error as e:
        logger.error("MinIO upload error: %s", e)
        raise


def get_presigned_download_url(object_name: str, expires_in_days: int = 7) -> str:
    """
    Get a presigned URL for downloading a file from MinIO.

    Args:
        object_name: Path in bucket (e.g., "profiles/user_123.jpg")
        expires_in_days: How many days the URL is valid (max 7 days)

    Returns:
        Presigned download URL

    Raises:
        S3Error: If URL generation fails
    """
    try:
        url = client.get_presigned_url(
            "GET",
            settings.MINIO_BUCKET,
            object_name,
            expires=timedelta(days=expires_in_days),
        )
        return url
    except S3Error as e:
        logger.error("MinIO presigned URL error: %s", e)
        raise


def delete_file(object_name: str) -> None:
    """
    Delete a file from MinIO.

    Args:
        object_name: Path in bucket

    Raises:
        S3Error: If deletion fails
    """
    try:
        client.remove_object(settings.MINIO_BUCKET, object_name)
        logger.info("Deleted file: %s", object_name)
    except S3Error as e:
        logger.error("MinIO delete error: %s", e)
        raise


def file_exists(object_name: str) -> bool:
    """Check if a file exists in MinIO."""
    try:
        client.stat_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error:
        return False
