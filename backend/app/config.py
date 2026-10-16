from __future__ import annotations

import base64
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

    # Cookies de YouTube (necesarias desde IPs de datacenter, p. ej. Render).
    # APP_COOKIES_TEXT: contenido Netscape cookies.txt
    # APP_COOKIES_B64: mismo contenido en base64 (más seguro para env vars)
    # APP_COOKIES_FILE: ruta a un cookies.txt ya existente
    cookies_file: Path | None = None
    cookies_text: str | None = None
    cookies_b64: str | None = None

    # Proxy opcional para yt-dlp (p. ej. un proxy residencial).
    ytdlp_proxy: str | None = None

    # Clientes de YouTube separados por coma (p. ej. "tv,web_safari").
    ytdlp_player_client: str | None = None


def _resolve_cookies(settings: Settings) -> Path | None:
    text = settings.cookies_text
    if not text and settings.cookies_b64:
        try:
            text = base64.b64decode(settings.cookies_b64).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            text = None
    if text:
        path = settings.downloads_dir / "cookies.txt"
        path.write_text(text, encoding="utf-8")
        return path
    if settings.cookies_file and settings.cookies_file.exists():
        return settings.cookies_file
    return None


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.downloads_dir.mkdir(parents=True, exist_ok=True)
    cookies = _resolve_cookies(settings)
    if cookies is not None:
        settings.cookies_file = cookies
    return settings
