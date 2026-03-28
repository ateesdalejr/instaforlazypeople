"""FastAPI application — Video Gen Service."""

import asyncio
import logging

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn

from models import VideoGenRequest, VideoGenResponse
import narrative_agent
import shot_planner
import video_generator
import editor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Gen Service", version="1.0.0")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "video_gen"}


@app.post("/generate", response_model=VideoGenResponse)
async def generate(request: VideoGenRequest):
    """Run the full 4-stage pipeline: narrative -> shots -> video clips -> final edit."""
    try:
        # Stage 1: Generate narrative from raw text
        logger.info("Stage 1: Generating narrative...")
        narrative = narrative_agent.generate_narrative(request.text)

        # Stage 2: Plan shots from narrative
        logger.info("Stage 2: Planning shots...")
        shots = shot_planner.plan_shots(narrative)

        # Stage 3: Generate video clips for each shot
        logger.info("Stage 3: Generating video clips (%d shots)...", len(shots))
        segments = await video_generator.generate_videos(shots)

        if not segments:
            raise HTTPException(status_code=500, detail="No video segments were generated")

        # Stage 4: Assemble final video
        logger.info("Stage 4: Assembling final video...")
        final = await editor.assemble_video(segments, shots)

        logger.info("Pipeline complete: %s (%.1fs)", final.video_path, final.duration_sec)

        return VideoGenResponse(
            video_path=final.video_path,
            duration_sec=final.duration_sec,
            narrative=narrative,
            shot_cards=shots,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/video/{filename}")
async def serve_video(filename: str):
    """Serve a generated video file."""
    import os

    path = os.path.join(editor.OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path, media_type="video/mp4")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
