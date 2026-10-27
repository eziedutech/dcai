"""Simple in-memory rate limits."""

import time
import uuid
from collections import deque


class RateLimiter:
    """Sliding window per key (a device, a guardian). In memory, one process."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self._hits: dict[uuid.UUID, deque[float]] = {}

    def allow(self, key: uuid.UUID) -> bool:
        now = time.monotonic()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] > 60:
            hits.popleft()
        if len(hits) >= self.per_minute:
            return False
        hits.append(now)
        return True
