from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Request

from app.schemas import InfoRequest, VideoInfo
from app.security import is_allowed_url

router = APIRouter(prefix="/info", tags=["info"])


@router.post("", response_model=VideoInfo)
async def video_info(payload: InfoRequest, request: Request) -> VideoInfo:
    if not is_allowed_url(payload.url):
        raise HTTPException(status_code=400, detail="URL no permitida")

    downloader = request.app.state.downloader
    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, downloader.extract_info, payload.url)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"No se pudo obtener la info: {exc}") from exc
    return VideoInfo(**info)
