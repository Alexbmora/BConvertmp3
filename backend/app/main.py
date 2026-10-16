from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.jobstore import InMemoryJobStore
from app.core.queue import JobQueue
from app.routers import info, jobs
from app.services.downloader import Downloader

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    job_store = InMemoryJobStore()
    downloader = Downloader(settings)
    job_queue = JobQueue(job_store, downloader, max_concurrent=settings.max_concurrent_jobs)
    await job_queue.start()

    app.state.settings = settings
    app.state.job_store = job_store
    app.state.downloader = downloader
    app.state.job_queue = job_queue

    try:
        yield
    finally:
        await job_queue.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix=settings.api_prefix)
app.include_router(info.router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
