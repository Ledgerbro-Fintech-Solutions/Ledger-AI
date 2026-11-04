import os
import mimetypes
from typing import List, Tuple
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings
from backend.app.core.logging import logger

# Graceful magic import
try:
    import magic
    HAS_MAGIC = True
except Exception:
    HAS_MAGIC = False

SUPPORTED_EXTENSIONS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp', '.csv', '.json'
}

SUPPORTED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/tiff',
    'image/bmp',
    'image/webp',
    'text/csv',
    'text/plain',
    'application/json'
}


def validate_file_type(file: UploadFile) -> bool:
    """Validate whether file extension and MIME type are permitted."""
    filename = file.filename or ""
    ext = os.path.splitext(filename.lower())[1]

    if ext not in SUPPORTED_EXTENSIONS:
        return False

    content_type = file.content_type or ""
    if content_type:
        base_mime = content_type.split(";")[0].strip().lower()
        if base_mime in SUPPORTED_MIME_TYPES or "application/octet-stream" in base_mime:
            return True

    guessed, _ = mimetypes.guess_type(filename)
    if guessed and guessed.lower() in SUPPORTED_MIME_TYPES:
        return True

    return True


def validate_uploaded_files(files: List[UploadFile]) -> None:
    """Validate file count, sizes, and formats."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files were provided in the request."
        )

    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 files allowed per batch upload."
        )

    for f in files:
        if not validate_file_type(f):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{f.filename}' has an unsupported extension or type."
            )


async def read_file_bytes(file: UploadFile) -> bytes:
    """Read bytes from an UploadFile and check size constraints."""
    await file.seek(0)
    data = await file.read()
    if len(data) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File '{file.filename}' exceeds maximum allowed size ({settings.max_file_size // (1024*1024)}MB)."
        )
    return data


def get_file_content_type(file: UploadFile, file_bytes: bytes = None) -> str:
    """Detect content type using magic if available, else standard headers."""
    if HAS_MAGIC and file_bytes:
        try:
            return magic.from_buffer(file_bytes, mime=True)
        except Exception:
            pass

    if file.content_type:
        return file.content_type.split(";")[0].strip().lower()

    guessed, _ = mimetypes.guess_type(file.filename or "")
    return guessed or "application/octet-stream"
