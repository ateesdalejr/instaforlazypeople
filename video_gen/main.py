"""FastAPI application — Video Gen Service.

Interface identical to get-video service:
  GET /data?days=1&maxResults=20  → returns .mp4 file
  GET /data/json                  → returns JSON with storyboard + clips + merged_video_path
"""

import logging
import traceback

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn

from models import PipelineResult, Storyboard, Scene, VideoClip
from pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Gen Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/data")
async def data(days: int = 1, maxResults: int = 20):
    """Run the full pipeline and return the merged video as an .mp4 download."""
    try:
        result = await run_pipeline(days, maxResults)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    if result.merged_video_path:
        return FileResponse(
            result.merged_video_path,
            media_type="video/mp4",
            filename="daily_video.mp4",
        )

    return result.model_dump()


@app.get("/data/json")
async def data_json(days: int = 1, maxResults: int = 20):
    """Same pipeline but always returns JSON."""
    try:
        result = await run_pipeline(days, maxResults)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return result.model_dump()


@app.get("/video/{filename}")
async def serve_video(filename: str):
    """Serve a generated video file."""
    import os
    from editor import OUTPUT_DIR
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path, media_type="video/mp4")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
