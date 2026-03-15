from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from backend.config import settings


UPLOAD_ROOT = Path(settings.uploads_dir)


def ensure_upload_root() -> Path:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    return UPLOAD_ROOT


def save_upload(upload: UploadFile, *, bucket: str, owner_id: str) -> dict[str, object]:
    root = ensure_upload_root()
    target_dir = root / bucket / owner_id
    target_dir.mkdir(parents=True, exist_ok=True)

    original_name = upload.filename or "archivo.bin"
    suffix = Path(original_name).suffix
    stored_name = f"{uuid4().hex}{suffix}"
    target_path = target_dir / stored_name

    with target_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    size = target_path.stat().st_size
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
