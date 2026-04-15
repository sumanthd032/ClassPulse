"""File upload routes."""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.file_attachment import FileAttachment
from app.models.user import User

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
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file. Returns file_id and download url."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not allowed",
        )

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB} MB)",
        )

    file_id = uuid.uuid4()
    upload_dir = Path(settings.UPLOAD_DIR) / str(file_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / (file.filename or "upload")
    dest.write_bytes(content)

    attachment = FileAttachment(
        id=file_id,
        uploader_id=current_user.id,
        original_filename=file.filename or "upload",
        stored_path=str(dest),
        file_size_bytes=len(content),
        mime_type=file.content_type,
    )
    db.add(attachment)
    await db.commit()

    return {
        "file_id": str(file_id),
        "filename": file.filename,
        "url": f"/api/v1/files/{file_id}",
        "size": len(content),
        "mime_type": file.content_type,
    }


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
    if not Path(attachment.stored_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk")
    return FileResponse(
        attachment.stored_path,
        media_type=attachment.mime_type or "application/octet-stream",
        filename=attachment.original_filename,
    )
