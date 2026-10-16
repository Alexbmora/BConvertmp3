from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}

ALLOWED_BITRATES = {"128", "192", "256", "320"}


def is_allowed_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    return host in ALLOWED_HOSTS


def safe_filename(name: str, fallback: str) -> str:
    invalid = '<>:"/\\|?*\n\r\t'
    cleaned = "".join("_" if c in invalid else c for c in name).strip().strip(".")
    cleaned = cleaned[:120]
    return cleaned or fallback


def resolve_output_path(raw: str) -> Path:
    return Path(raw)
