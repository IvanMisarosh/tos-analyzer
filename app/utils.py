from fastapi import UploadFile
from pathlib import Path
from app.config import settings


async def save_upload_file(upload_file: UploadFile) -> str:
    uploads_folder: Path = settings.UPLOADS_FOLDER
    uploads_folder.mkdir(parents=True, exist_ok=True)
    file_path = uploads_folder / upload_file.filename

    with open(file_path, "wb") as buffer:
        while chunk := await upload_file.read(1024 * 1024):
            buffer.write(chunk)
    await upload_file.close()
    return str(file_path)
