from __future__ import annotations

import asyncio
import logging

from app.core.jobstore import JobStore
from app.schemas import JobStatus

logger = logging.getLogger(__name__)


class JobQueue:
    """Cola en proceso con N workers.

    Cada worker ejecuta yt-dlp en un hilo aparte (es bloqueante). En la Fase 2
    esto se sustituye por un consumer en un servicio Worker separado que lee
    de Postgres con SELECT ... FOR UPDATE SKIP LOCKED.
    """

    def __init__(self, store: JobStore, downloader, max_concurrent: int = 2) -> None:
        self._store = store
        self._downloader = downloader
        self._max = max(1, max_concurrent)
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []

    async def start(self) -> None:
        self._workers = [
            asyncio.create_task(self._worker(i), name=f"job-worker-{i}")
            for i in range(self._max)
        ]

    async def stop(self) -> None:
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def enqueue(self, job_id: str) -> None:
        await self._queue.put(job_id)

    async def _worker(self, index: int) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                await self._process(job_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Worker %s falló procesando job %s", index, job_id)
            finally:
                self._queue.task_done()

    async def _process(self, job_id: str) -> None:
        job = self._store.get(job_id)
        if job is None:
            return

        self._store.update(job_id, status=JobStatus.downloading, progress=0.0)

        def on_progress(data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                progress = (downloaded / total * 100.0) if total else 0.0
                self._store.update(
                    job_id,
                    progress=round(progress, 2),
                    speed=data.get("_speed_str"),
                    eta=data.get("eta"),
                )
            elif status == "finished":
                self._store.update(job_id, status=JobStatus.converting, progress=100.0)

        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None, self._downloader.download, job, on_progress
            )
        except Exception as exc:
            logger.exception("Job %s falló", job_id)
            self._store.update(job_id, status=JobStatus.failed, error=str(exc))
            return

        self._store.update(
            job_id,
            status=JobStatus.completed,
            progress=100.0,
            file_path=result["file_path"],
            title=result.get("title"),
            uploader=result.get("uploader"),
            duration=result.get("duration"),
            thumbnail_url=result.get("thumbnail"),
            speed=None,
            eta=None,
        )
