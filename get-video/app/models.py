from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


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


class Scene(BaseModel):
    scene_number: int
    description: str       # Text-to-video prompt
    duration_seconds: float = 5.0


class Storyboard(BaseModel):
    title: str
    summary: str
    scenes: list[Scene]


class VideoClip(BaseModel):
    scene_number: int
    request_id: Optional[str] = None
    status: str
    video_url: Optional[str] = None
    error: Optional[str] = None


class PipelineResult(BaseModel):
    storyboard: Storyboard
    clips: list[VideoClip]
    merged_video_path: Optional[str] = None
