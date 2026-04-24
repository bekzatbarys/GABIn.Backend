import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse as FastAPIFileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas.file import FileResponse
from app.utils.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/files", tags=["Files"])

ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf", "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="File type not allowed")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, unique_filename)

    os.makedirs(settings.upload_dir, exist_ok=True)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)

    db_file = FileModel(
        filename=unique_filename,
        original_name=file.filename,
        content_type=file.content_type,
        size=len(contents),
        path=file_path,
        owner_id=current_user.id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


@router.get("/", response_model=List[FileResponse])
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(FileModel).filter(FileModel.owner_id == current_user.id).all()


@router.get("/{file_id}/download")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.owner_id == current_user.id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(db_file.path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FastAPIFileResponse(db_file.path, filename=db_file.original_name)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_file = db.query(FileModel).filter(FileModel.id == file_id, FileModel.owner_id == current_user.id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    if os.path.exists(db_file.path):
        os.remove(db_file.path)
    db.delete(db_file)
    db.commit()
