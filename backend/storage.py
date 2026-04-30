from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from backend.config import settings


UPLOAD_ROOT = Path(settings.uploads_dir)
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}


def ensure_upload_root() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def save_upload(upload: UploadFile, *, bucket: str, owner_id: str) -> dict[str, object]:
    root = ensure_upload_root()
    target_dir = root / bucket / owner_id
    target_dir.mkdir(parents=True, exist_ok=True)

    original_name = upload.filename or "archivo.bin"
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido. Usa PDF, DOC, DOCX, JPG o PNG.",
        )
    stored_name = f"{uuid4().hex}{suffix}"
    target_path = target_dir / stored_name

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    size = target_path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Archivo demasiado grande. Maximo permitido: 15 MB.",
        )

    relative_path = target_path.relative_to(root).as_posix()
    return {
        "original_name": original_name,
        "stored_name": stored_name,
        "relative_path": relative_path,
        "mime_type": upload.content_type or "application/octet-stream",
        "file_size": size,
    }


def move_relative_path(relative_path: str, *, bucket: str, owner_id: str) -> str:
    root = ensure_upload_root()
    current_path = root / relative_path
    if not current_path.exists():
        return relative_path

    target_dir = root / bucket / owner_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / current_path.name
    if target_path == current_path:
        return relative_path

    current_path.replace(target_path)
    return target_path.relative_to(root).as_posix()


def absolute_path(relative_path: str) -> Path:
    return ensure_upload_root() / relative_path
