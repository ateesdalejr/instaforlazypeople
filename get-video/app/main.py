import json
import logging
import os
import traceback
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .models import PipelineResult
from .pipeline import run_pipeline

log = logging.getLogger(__name__)

app = FastAPI(title="Gmail Video Service")

CACHE_DIR = os.getenv("CACHE_DIR", "./cache")


def _cache_key(days: int, max_results: int) -> str:
    return f"{date.today().isoformat()}_d{days}_m{max_results}"


def _cache_path(key: str) -> str:
    return os.path.join(CACHE_DIR, f"{key}.json")


def _get_cached(days: int, max_results: int) -> PipelineResult | None:
    path = _cache_path(_cache_key(days, max_results))
    if os.path.exists(path):
        log.info(f"[cache] HIT: {path}")
        with open(path) as f:
            return PipelineResult.model_validate_json(f.read())
    return None


def _set_cache(days: int, max_results: int, result: PipelineResult) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(_cache_key(days, max_results))
    with open(path, "w") as f:
        f.write(result.model_dump_json())
    log.info(f"[cache] STORED: {path}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data")
def data(days: int = 1, maxResults: int = 20, bust_cache: bool = False):
    """
    Run the full pipeline and return the merged video as an .mp4 download.
    Falls back to JSON if video generation fails.
    """
    try:
        cached = None if bust_cache else _get_cached(days, maxResults)
        result = cached or run_pipeline(days, maxResults)
        if not cached:
            _set_cache(days, maxResults, result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if result.merged_video_path:
        return FileResponse(
            result.merged_video_path,
            media_type="video/mp4",
            filename="daily_video.mp4",
        )

    # Fallback if all clips failed
    return result.model_dump()


@app.get("/data/json")
def data_json(days: int = 1, maxResults: int = 20, bust_cache: bool = False):
    """
    Same pipeline but always returns JSON — useful for debugging.
    Returns storyboard, individual clip URLs, and merged video path.
    """
    try:
        cached = None if bust_cache else _get_cached(days, maxResults)
        result = cached or run_pipeline(days, maxResults)
        if not cached:
            _set_cache(days, maxResults, result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result.model_dump()
