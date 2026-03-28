from datetime import datetime
from pydantic import BaseModel, Field


class Media(BaseModel):
    link: str | None = Field(None, description="URL to attach to the post")
    description: str | None = Field(None, description="Description of the link or media")
    title: str | None = Field(None, description="Title for the attachment")
    picture: str | None = Field(None, description="URL of a preview image for a link")
    photo: str | None = Field(None, description="URL of a photo to post directly")
    thumbnail: str | None = Field(None, description="Thumbnail image URL")


class Retweet(BaseModel):
    tweet_id: str = Field(..., description="ID of the tweet to retweet")
    comment: str | None = Field(None, description="Optional quote-tweet comment")


class CreateUpdate(BaseModel):
    """Request body for POST https://api.bufferapp.com/1/updates/create.json"""

    profile_ids: list[str] = Field(..., description="Buffer profile IDs to post to")
    text: str | None = Field(None, description="Text content of the post")
    shorten: bool = Field(True, description="Auto-shorten links in text")
    now: bool = Field(False, description="Publish immediately instead of queuing")
    top: bool = Field(False, description="Add to top of queue (next to publish)")
    scheduled_at: datetime | None = Field(
        None,
        description="Specific publish time (overrides now and top)",
    )
    media: Media | None = Field(None, description="Media attachment")
    attachment: bool = Field(
        True,
        description="Auto-populate media from link in text",
    )
    retweet: Retweet | None = Field(None, description="Twitter retweet data")


class UpdateResponse(BaseModel):
    """Single update object returned by the Buffer API."""

    id: str
    created_at: int
    profile_id: str
    status: str
    text: str
    via: str


class CreateUpdateResponse(BaseModel):
    """Response from POST /1/updates/create.json"""

    success: bool
    buffer_count: int
    buffer_percentage: int
    updates: list[UpdateResponse]
