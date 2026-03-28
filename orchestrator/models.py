"""
Models for the orchestrator service.

These mirror the shapes returned by the downstream services so we can
validate responses without importing their code directly.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


# -- get-video response shapes ------------------------------------------------

class Scene(BaseModel):
    scene_number: int
    description: str
    duration_seconds: float = 5.0


class Storyboard(BaseModel):
    title: str
    summary: str
    scenes: List[Scene]


class VideoClip(BaseModel):
    scene_number: int
    request_id: Optional[str] = None
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None


class VideoDataResponse(BaseModel):
    storyboard: Storyboard
    clips: List[VideoClip]
    merged_video_path: Optional[str] = None


# -- polisher caption shapes --------------------------------------------------

class CaptionInput(BaseModel):
    script: str
    video_url: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = "engaging"


class CaptionAgentOutput(BaseModel):
    caption: str
    metadata: dict = Field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None


# -- buffer shapes -------------------------------------------------------------

class Media(BaseModel):
    link: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    picture: Optional[str] = None
    photo: Optional[str] = None
    video: Optional[str] = None
    thumbnail: Optional[str] = None


class CreateUpdate(BaseModel):
    profile_ids: List[str]
    text: Optional[str] = None
    shorten: bool = True
    now: bool = False
    top: bool = False
    media: Optional[Media] = None


# -- orchestrator own response -------------------------------------------------

class StepResult(BaseModel):
    step: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class PipelineResponse(BaseModel):
    success: bool
    steps: List[StepResult]
    video: Optional[VideoDataResponse] = None
    caption: Optional[CaptionAgentOutput] = None
    buffer_response: Optional[dict] = None
