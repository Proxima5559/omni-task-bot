from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models import TaskSource, TaskStatus, TranscriptionStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    title: str
    description: str | None
    status: TaskStatus
    source: TaskSource
    transcription_status: TranscriptionStatus
    transcription_error: str | None
    created_at: datetime
    updated_at: datetime