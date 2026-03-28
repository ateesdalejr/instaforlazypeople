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
    Scene,
    StepResult,
    Storyboard,
    VideoClip,
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


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def _mock_video() -> VideoDataResponse:
    """Return a realistic-looking VideoDataResponse with fake data."""
    return VideoDataResponse(
        storyboard=Storyboard(
            title="Day in the Life of a Developer",
            summary=(
                "Follow a software developer from the first sip of morning coffee "
                "through a marathon debugging session to the triumphant moment the "
                "CI pipeline finally goes green."
            ),
            scenes=[
                Scene(
                    scene_number=1,
                    description=(
                        "Developer opens laptop at a cozy desk, coffee in hand. "
                        "The IDE boots up, dozens of terminal tabs spring to life."
                    ),
                    duration_seconds=5.0,
                ),
                Scene(
                    scene_number=2,
                    description=(
                        "Close-up of furious typing as a tricky bug is hunted down. "
                        "Stack traces scroll past; sticky notes pile up on the monitor."
                    ),
                    duration_seconds=6.0,
                ),
                Scene(
                    scene_number=3,
                    description=(
                        "The CI build turns green. Developer leans back with a "
                        "satisfied grin, pushes to main, and closes the laptop."
                    ),
                    duration_seconds=4.0,
                ),
            ],
        ),
        clips=[
            VideoClip(
                scene_number=1,
                request_id="mock-req-001",
                status="completed",
                video_url="https://example.com/clips/morning-coffee.mp4",
            ),
            VideoClip(
                scene_number=2,
                request_id="mock-req-002",
                status="completed",
                video_url="https://example.com/clips/debugging-session.mp4",
            ),
            VideoClip(
                scene_number=3,
                request_id="mock-req-003",
                status="completed",
                video_url="https://example.com/clips/ci-green.mp4",
            ),
        ],
        merged_video_path="https://example.com/merged/day-in-the-life-final.mp4",
    )


def _mock_caption() -> CaptionAgentOutput:
    """Return a realistic-looking CaptionAgentOutput with fake data."""
    return CaptionAgentOutput(
        caption=(
            "Ever mass-close 47 browser tabs because your bug was a typo? "
            "Same. \U0001f602\u2615\n\n"
            "Here's what a real day of coding actually looks like -- "
            "from that first coffee hit to the sweet, sweet green CI build. "
            "No glamour shots, just vibes.\n\n"
            "\U0001f449 Save this for the next time someone asks what you do all day.\n\n"
            "#devlife #coding #softwareengineer #dayinthelife #programming "
            "#buildinpublic #techlife #developer #webdev #100daysofcode"
        ),
        metadata={
            "hook": "Ever mass-close 47 browser tabs because your bug was a typo?",
            "cta": "Save this for the next time someone asks what you do all day.",
            "hashtag_count": 10,
            "tone": "engaging",
        },
        success=True,
    )


def _mock_buffer_response() -> dict:
    """Return a realistic-looking buffer response dict."""
    return {
        "success": True,
        "id": "mock-update-123",
        "message": "Update created successfully (mock).",
        "profile_id": "mock-profile-456",
        "scheduled_at": "2026-03-28T18:00:00Z",
    }


# ---------------------------------------------------------------------------
# Mock endpoints
# ---------------------------------------------------------------------------


@app.get("/run/mock")
async def run_pipeline_mock():
    """Return a complete PipelineResponse with fake test data (no real calls)."""
    return PipelineResponse(
        success=True,
        steps=[
            StepResult(step="get-video", success=True),
            StepResult(step="polisher", success=True),
            StepResult(step="buffer", success=True),
        ],
        video=_mock_video(),
        caption=_mock_caption(),
        buffer_response=_mock_buffer_response(),
    )


@app.get("/mock/video")
async def mock_video():
    """Return a VideoDataResponse with fake test data."""
    return _mock_video()


@app.get("/mock/caption")
async def mock_caption():
    """Return a CaptionAgentOutput with fake test data."""
    return _mock_caption()


@app.get("/mock/buffer")
async def mock_buffer():
    """Return a mock buffer CreateUpdateResponse."""
    return _mock_buffer_response()


# ---------------------------------------------------------------------------
# Static files & UI
# ---------------------------------------------------------------------------

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


@app.get("/")
async def root():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
