import asyncio
import time
from collections import defaultdict

from exceptions import RateLimitExceededError


class PerUserRateLimiter:
    """In-memory sliding window rate limiter. Keyed by user_id."""

    def __init__(self, rpm: int = 60):
        self._rpm = rpm
        self._window = 60.0  # seconds
        self._timestamps: dict[str, list[float]] = defaultdict(list)
        self._max_wait = 30.0  # seconds

    async def acquire(self, user_id: str) -> None:
        """Wait until a request slot is available, or raise if wait is too long."""
        now = time.monotonic()
        cutoff = now - self._window

        # Prune old timestamps
        self._timestamps[user_id] = [
            t for t in self._timestamps[user_id] if t > cutoff
        ]

        if len(self._timestamps[user_id]) < self._rpm:
            self._timestamps[user_id].append(now)
            return

        # Calculate wait time until the oldest request falls out of window
        oldest = self._timestamps[user_id][0]
        wait = oldest + self._window - now

        if wait > self._max_wait:
            raise RateLimitExceededError(
                f"Rate limit for user {user_id}: would need to wait {wait:.1f}s"
            )

        await asyncio.sleep(wait)
        # Prune again after sleeping
        now = time.monotonic()
        self._timestamps[user_id] = [
            t for t in self._timestamps[user_id] if t > now - self._window
        ]
        self._timestamps[user_id].append(now)
