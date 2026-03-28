from pydantic import BaseModel


class PostResult(BaseModel):
    """What this service returns after creating a Buffer post."""

    success: bool
    post_id: str | None = None
    status: str | None = None
    error: str | None = None
