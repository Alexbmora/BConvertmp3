from __future__ import annotations

import logging
from pathlib import Path

import yt_dlp

from app.config import Settings
from app.core.jobstore import Job

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _base_options(self) -> dict:
        options: dict = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "noprogress": True,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 30,
        }
        if self.settings.ffmpeg_location:
            options["ffmpeg_location"] = self.settings.ffmpeg_location
        if self.settings.cookies_file and Path(self.settings.cookies_file).exists():
            options["cookiefile"] = str(self.settings.cookies_file)
        if self.settings.ytdlp_proxy:
            options["proxy"] = self.settings.ytdlp_proxy
        if self.settings.ytdlp_player_client:
            clients = [
                c.strip()
                for c in self.settings.ytdlp_player_client.split(",")
                if c.strip()
            ]
            if clients:
                options["extractor_args"] = {"youtube": {"player_client": clients}}
        return options

    def _open(self, options: dict) -> yt_dlp.YoutubeDL:
        ydl = yt_dlp.YoutubeDL(options)
        # Fuerza la carga del cookiejar y luego anula cookiefile para que yt-dlp
        # NO reescriba el archivo (evita que pode/expire cookies en cada corrida).
        if options.get("cookiefile"):
            _ = ydl.cookiejar
            ydl.params["cookiefile"] = None
        return ydl

    def extract_info(self, url: str) -> dict:
        options = {**self._base_options(), "skip_download": True}
        with self._open(options) as ydl:
            info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "webpage_url": info.get("webpage_url"),
        }

    def download(self, job: Job, on_progress) -> dict:
        outtmpl = str(self.settings.downloads_dir / f"{job.id}.%(ext)s")
        options = {
            **self._base_options(),
            "format": "bestaudio/best",
            "outtmpl": outtmpl,
            "writethumbnail": True,
            "progress_hooks": [on_progress],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": job.bitrate,
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "EmbedThumbnail", "already_have_thumbnail": False},
            ],
        }
        with self._open(options) as ydl:
            info = ydl.extract_info(job.url, download=True)

        file_path = self.settings.downloads_dir / f"{job.id}.mp3"
        if not file_path.exists():
            raise FileNotFoundError("yt-dlp no generó el archivo MP3")

        return {
            "file_path": str(file_path),
            "title": info.get("title"),
            "uploader": info.get("uploader") or info.get("channel"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
        }
