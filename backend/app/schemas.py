from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security import ALLOWED_BITRATES


class JobStatus(str, Enum):
    queued = "queued"
    downloading = "downloading"
    converting = "converting"
    completed = "completed"
    failed = "failed"


class JobCreate(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=50)
    bitrate: str = Field(default="192")

    @field_validator("bitrate")
    @classmethod
    def validate_bitrate(cls, value: str) -> str:
        if value not in ALLOWED_BITRATES:
            raise ValueError(f"Bitrate no soportado. Opciones: {sorted(ALLOWED_BITRATES)}")
        return value


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    url: str
    bitrate: str
    status: JobStatus
    title: str | None = None
    uploader: str | None = None
    duration: int | None = None
    thumbnail_url: str | None = None
    progress: float = 0.0
    speed: str | None = None
    eta: int | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class InfoRequest(BaseModel):
    url: str


class VideoInfo(BaseModel):
    title: str | None = None
    uploader: str | None = None
    duration: int | None = None
    thumbnail: str | None = None
    webpage_url: str | None = None
