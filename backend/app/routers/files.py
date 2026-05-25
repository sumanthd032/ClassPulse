"""File upload routes with MinIO storage."""
import logging
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.file_attachment import FileAttachment
from app.models.user import User
from app.utils.minio_client import upload_file, get_presigned_download_url, delete_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Files"])

ALLOWED_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/zip",
    "application/x-zip-compressed",
}


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload a file")
async def upload_file_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file to MinIO storage. Returns file_id and download url."""
    try:
        logger.info(f"Upload started: user={current_user.id}, filename={file.filename}, content_type={file.content_type}")
        
        if file.content_type not in ALLOWED_TYPES:
            logger.warning(f"Rejected file type: {file.content_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file.content_type}' is not allowed",
            )

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        content = await file.read()
        if len(content) > max_size:
            logger.warning(f"File too large: {len(content)} > {max_size}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB)",
            )

        file_id = uuid.uuid4()
        object_name = f"files/{file_id}/{file.filename or 'upload'}"

        # Upload to MinIO
        logger.info(f"Uploading to MinIO: {object_name}")
        upload_file(content, object_name)

        # Record in database
        attachment = FileAttachment(
            id=file_id,
            uploader_id=current_user.id,
            original_filename=file.filename or "upload",
            stored_path=object_name,  # Store MinIO path
            file_size_bytes=len(content),
            mime_type=file.content_type,
        )
        db.add(attachment)
        await db.commit()
        logger.info(f"File recorded in database: {file_id}")

        # Get presigned download URL
        download_url = get_presigned_download_url(object_name)
        logger.info(f"Upload successful: {file_id}")

        return {
            "file_id": str(file_id),
            "filename": file.filename,
            "url": download_url,
            "size": len(content),
            "mime_type": file.content_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Upload error: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload failed: {str(e)}",
        )


@router.get("/files/{file_id}", summary="Download a file")
async def download_file(
    file_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(FileAttachment).where(FileAttachment.id == file_id))
    attachment = result.scalars().first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    try:
        # Get presigned URL from MinIO
        download_url = get_presigned_download_url(attachment.stored_path)
        return {"url": download_url, "filename": attachment.original_filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}",
        )
