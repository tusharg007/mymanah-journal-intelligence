from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from .errors import ServiceError


class Admission:
    def __init__(self, queue_size: int = 2):
        self.slots = asyncio.Semaphore(1)
        self.count = 0
        self.limit = 1 + queue_size
        self.requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def rate(self, principal: str, kind: str, limit: int) -> None:
        now = time.monotonic()
        history = self.requests[principal, kind]
        while history and now - history[0] >= 60:
            history.popleft()
        if len(history) >= limit:
            raise ServiceError("RATE_LIMITED", "Request rate exceeded; retry later", 429)
        history.append(now)

    @asynccontextmanager
    async def enter(self):
        if self.count >= self.limit:
            raise ServiceError("QUEUE_FULL", "Inference capacity is busy; retry later", 429)
        self.count += 1
        try:
            await self.slots.acquire()
            try:
                yield
            finally:
                self.slots.release()
        finally:
            self.count -= 1
