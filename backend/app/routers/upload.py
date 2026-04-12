import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.models.schemas import UploadResponse

router = APIRouter()

ALLOWED_SUFFIXES = {".mp4", ".mov", ".avi", ".mkv", ".webm"}


@router.post("/upload", response_model=UploadResponse)
async def upload(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, f"unsupported file type: {suffix or '<none>'}")

    upload_dir: Path = request.app.state.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    task_manager = request.app.state.task_manager
    task_id = task_manager.create_task(video_path="")
    dest = upload_dir / f"{task_id}{suffix}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    task_manager.tasks[task_id].video_path = str(dest)

    await task_manager.enqueue(task_id)
    return UploadResponse(task_id=task_id)
