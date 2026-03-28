"""
Pydantic models for the video_gen service.

Interface is identical to get-video service so orchestrator can swap between them.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input (matches get-video)
# ---------------------------------------------------------------------------

class VideoDataRequest(BaseModel):
    days: int = Field(default=1, ge=1)
    max_results: int = Field(default=20, ge=1, le=100, alias="maxResults")
    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Source data (mirrors get-video)
# ---------------------------------------------------------------------------

class Email(BaseModel):
    id: str
    date: str
    from_: Optional[str] = Field(None, alias="from")
    subject: str
    snippet: str
    body: str
    model_config = {"populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "from" in obj:
            obj = {**obj, "from_": obj.pop("from")}
        return super().model_validate(obj, *args, **kwargs)


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None
    attendees: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Storyboard / Scenes (matches get-video)
# ---------------------------------------------------------------------------

class Scene(BaseModel):
    scene_number: int
    description: str
    duration_seconds: float = 3.0


class Storyboard(BaseModel):
    title: str
    summary: str
    scenes: list[Scene]


# ---------------------------------------------------------------------------
# Video clips (matches get-video)
# ---------------------------------------------------------------------------

class VideoClip(BaseModel):
    scene_number: int
    request_id: Optional[str] = None
    status: str             # "completed" | "failed" | "processing"
    video_url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Response (matches get-video PipelineResult)
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    storyboard: Storyboard
    clips: list[VideoClip]
    merged_video_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Internal models (used between stages, not in API)
# ---------------------------------------------------------------------------

class Beat(BaseModel):
    timestamp: str
    summary: str
    raw_quote: str
    beat_type: str
    drama_score: int


class Narrative(BaseModel):
    cold_open: str
    acts: list[list[Beat]]
    closing_hook: str
    persona_quirks: list[str]


class ShotCard(BaseModel):
    shot_id: int
    visual_prompt: str
    voiceover_text: str
    subtitle_text: str
    duration_sec: float = 3.0


class VideoSegment(BaseModel):
    shot_id: int
    video_url: str
    duration_sec: float


class FinalVideo(BaseModel):
    video_path: str
    duration_sec: float
