from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    task_id: str


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str
    error: str | None = None


class TrackInfo(BaseModel):
    track_id: int
    frame_count: int


class TracksResponse(BaseModel):
    task_id: str
    tracks: list[TrackInfo]


class ConvertRequest(BaseModel):
    track_id: int
    fps: int = Field(default=30, ge=1, le=240)
    smoothing: bool = False


class ConvertResponse(BaseModel):
    task_id: str
    status: str
