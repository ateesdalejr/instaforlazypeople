class BufferServiceError(Exception):
    """Base for all buffer service errors."""

    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class BufferAPIError(BufferServiceError):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Buffer API error: {message}")


class RateLimitExceededError(BufferServiceError):
    status_code = 429
    detail = "Rate limit exceeded. Try again later."


class MissingConfigError(BufferServiceError):
    status_code = 503
    detail = "Buffer access token or channel ID not configured."
