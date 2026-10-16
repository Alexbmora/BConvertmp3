from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from app.schemas import JobCreate, JobRead, JobStatus
from app.security import is_allowed_url, resolve_output_path, safe_filename

router = APIRouter(prefix="/jobs", tags=["jobs"])

TERMINAL_STATUSES = {JobStatus.completed, JobStatus.failed}


@router.post("", response_model=list[JobRead], status_code=201)
async def create_jobs(payload: JobCreate, request: Request) -> list[JobRead]:
    store = request.app.state.job_store
    queue = request.app.state.job_queue

    jobs = []
    for url in payload.urls:
        if not is_allowed_url(url):
            raise HTTPException(status_code=400, detail=f"URL no permitida: {url}")
        jobs.append(store.add(url=url, bitrate=payload.bitrate))

    for job in jobs:
        await queue.enqueue(job.id)

    return jobs


@router.get("", response_model=list[JobRead])
async def list_jobs(request: Request) -> list[JobRead]:
    store = request.app.state.job_store
    return store.list()


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: str, request: Request) -> JobRead:
    store = request.app.state.job_store
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


@router.get("/{job_id}/events")
async def job_events(job_id: str, request: Request) -> EventSourceResponse:
    store = request.app.state.job_store
    if store.get(job_id) is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    async def event_generator():
        last: str | None = None
        while True:
            if await request.is_disconnected():
                break
            job = store.get(job_id)
            if job is None:
                break
            payload = json.dumps(JobRead.model_validate(job).model_dump(mode="json"))
            if payload != last:
                last = payload
                yield {"event": "update", "data": payload}
            if job.status in TERMINAL_STATUSES:
                yield {"event": "done", "data": payload}
                break
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@router.get("/{job_id}/download")
async def download_job(job_id: str, request: Request) -> FileResponse:
    store = request.app.state.job_store
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if job.status != JobStatus.completed or not job.file_path:
        raise HTTPException(status_code=409, detail="El job todavía no está listo")

    path = resolve_output_path(job.file_path)
    if not path.exists():
        raise HTTPException(status_code=410, detail="El archivo ya no está disponible")

    filename = f"{safe_filename(job.title or job.id, job.id)}.mp3"
    return FileResponse(path, media_type="audio/mpeg", filename=filename)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str, request: Request) -> None:
    store = request.app.state.job_store
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if job.file_path:
        path = resolve_output_path(job.file_path)
        path.unlink(missing_ok=True)
    store.delete(job_id)
