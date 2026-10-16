from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas import JobStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Job:
    id: str
    url: str
    bitrate: str
    status: JobStatus = JobStatus.queued
    title: str | None = None
    uploader: str | None = None
    duration: int | None = None
    thumbnail_url: str | None = None
    progress: float = 0.0
    speed: str | None = None
    eta: int | None = None
    file_path: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)


class JobStore(ABC):
    @abstractmethod
    def add(self, url: str, bitrate: str) -> Job: ...

    @abstractmethod
    def get(self, job_id: str) -> Job | None: ...

    @abstractmethod
    def list(self) -> list[Job]: ...

    @abstractmethod
    def update(self, job_id: str, **fields) -> Job | None: ...

    @abstractmethod
    def delete(self, job_id: str) -> bool: ...


class InMemoryJobStore(JobStore):
    """Implementación volátil para el MVP.

    Se reemplazará por PostgresJobStore (Supabase) en la Fase 2 sin tocar
    los routers: basta con respetar la interfaz JobStore.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def add(self, url: str, bitrate: str) -> Job:
        job = Job(id=uuid4().hex, url=url, bitrate=bitrate)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def update(self, job_id: str, **fields) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in fields.items():
                setattr(job, key, value)
            job.updated_at = _now()
            return job

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None
