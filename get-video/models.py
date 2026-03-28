"""
Pydantic models for the GET /data endpoint of the get-video service.

This service reads Gmail emails and Google Calendar events for the last N days,
generates a storyboard via Claude, produces video clips via GMI Cloud wan2.1-t2v,
merges them with ffmpeg, and returns the completed MP4.

Usage (other services):
    import requests
    from get_video.models import VideoDataRequest, VideoDataResponse

    response = requests.get("http://get-video:8004/data", params={"days": 3})
    data = VideoDataResponse.model_validate(response.json())
    print(data.merged_video_path)
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------

class VideoDataRequest(BaseModel):
    """Query parameters accepted by GET /data"""
    days: int = Field(default=1, ge=1, description="How many days back to pull emails and events")
    max_results: int = Field(default=20, ge=1, le=100, alias="maxResults", description="Max emails to fetch")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# Source data (mirrors gmail/models.py so other services share the same shape)
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
    attendees: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Storyboard (Claude output)
# ---------------------------------------------------------------------------

class Scene(BaseModel):
    scene_number: int
    description: str        # Text-to-video prompt sent to GMI Cloud
    duration_seconds: float = 5.0


class Storyboard(BaseModel):
    title: str
    summary: str
    scenes: List[Scene]


# ---------------------------------------------------------------------------
# Video generation (GMI Cloud wan2.1-t2v)
# ---------------------------------------------------------------------------

class VideoClip(BaseModel):
    scene_number: int
    request_id: Optional[str] = None
    status: str             # "completed" | "failed" | "processing"
    video_url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class VideoDataResponse(BaseModel):
    """Full response returned by GET /data?days=N"""
    storyboard: Storyboard
    clips: List[VideoClip]
    merged_video_path: Optional[str] = Field(
        None,
        description="Local path to the merged MP4 file on the server"
    )
