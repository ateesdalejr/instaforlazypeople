"""
Orchestrator service — runs the get-video -> polisher -> buffer pipeline.
"""

import logging
import os

import httpx
from fastapi import FastAPI

from models import (
    CaptionAgentOutput,
    CaptionInput,
    CreateUpdate,
    Media,
    PipelineResponse,
    StepResult,
    VideoDataResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Orchestrator", version="1.0.0")

# ---------------------------------------------------------------------------
# Config from env
# ---------------------------------------------------------------------------

GET_VIDEO_URL = os.getenv("GET_VIDEO_URL", "http://get-video:8000")
POLISHER_URL = os.getenv("POLISHER_URL", "http://polisher:8000")
BUFFER_URL = os.getenv("BUFFER_URL", "http://buffer:8000")

BUFFER_PROFILE_IDS = os.getenv("BUFFER_PROFILE_IDS", "")  # comma-separated
TARGET_AUDIENCE = os.getenv("TARGET_AUDIENCE", "general audience")
CAPTION_TONE = os.getenv("CAPTION_TONE", "engaging")

# Timeout for each downstream call (seconds)
SERVICE_TIMEOUT = float(os.getenv("SERVICE_TIMEOUT", "300"))


def _profile_ids() -> list[str]:
    return [pid.strip() for pid in BUFFER_PROFILE_IDS.split(",") if pid.strip()]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator"}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


@app.post("/run")
async def run_pipeline(days: int = 1, max_results: int = 20):
    """Execute the full pipeline: get-video -> polisher -> buffer."""

    steps: list[StepResult] = []
    video_data: VideoDataResponse | None = None
    caption_output: CaptionAgentOutput | None = None
    buffer_resp: dict | None = None
    pipeline_ok = True

    async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT) as client:
        # ---- Step 1: get-video ----
        try:
            resp = await client.get(
                f"{GET_VIDEO_URL}/data/json",
                params={"days": days, "maxResults": max_results},
            )
            resp.raise_for_status()
            video_data = VideoDataResponse.model_validate(resp.json())
            steps.append(StepResult(step="get-video", success=True))
        except Exception as exc:
            logger.exception("get-video failed")
            steps.append(
                StepResult(step="get-video", success=False, error=str(exc))
            )
            pipeline_ok = False
            # Cannot continue without video data
            return PipelineResponse(
                success=False,
                steps=steps,
            )

        # ---- Step 2: polisher (best-effort) ----
        try:
            caption_input = CaptionInput(
                script=video_data.storyboard.summary,
                video_url=video_data.merged_video_path,
                target_audience=TARGET_AUDIENCE,
                tone=CAPTION_TONE,
            )
            resp = await client.post(
                f"{POLISHER_URL}/caption/generate",
                json=caption_input.model_dump(),
            )
            resp.raise_for_status()
            caption_output = CaptionAgentOutput.model_validate(resp.json())
            steps.append(StepResult(step="polisher", success=True))
        except Exception as exc:
            logger.exception("polisher failed — continuing without caption")
            steps.append(
                StepResult(step="polisher", success=False, error=str(exc))
            )
            # Don't abort; polisher is optional

        # ---- Step 3: buffer ----
        try:
            profile_ids = _profile_ids()
            if not profile_ids:
                raise ValueError(
                    "BUFFER_PROFILE_IDS env var is empty — cannot post to Buffer"
                )

            post_text = (
                caption_output.caption
                if caption_output and caption_output.success
                else video_data.storyboard.summary
            )

            media = None
            if video_data.merged_video_path:
                media = Media(photo=video_data.merged_video_path)

            create_update = CreateUpdate(
                profile_ids=profile_ids,
                text=post_text,
                now=False,
                media=media,
            )
            resp = await client.post(
                f"{BUFFER_URL}/v1/posts",
                json=create_update.model_dump(exclude_none=True),
            )
            resp.raise_for_status()
            buffer_resp = resp.json()
            steps.append(StepResult(step="buffer", success=True))
        except Exception as exc:
            logger.exception("buffer failed")
            steps.append(
                StepResult(step="buffer", success=False, error=str(exc))
            )
            pipeline_ok = False

    return PipelineResponse(
        success=pipeline_ok,
        steps=steps,
        video=video_data,
        caption=caption_output,
        buffer_response=buffer_resp,
    )
