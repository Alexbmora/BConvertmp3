from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "YouTube MP3 API"
    api_prefix: str = "/api/v1"
    debug: bool = False

    downloads_dir: Path = BASE_DIR / "downloads"
    default_bitrate: str = "192"
    max_concurrent_jobs: int = 2

    cors_origins: list[str] = ["http://localhost:5173"]
    ffmpeg_location: str | None = None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    return settings
