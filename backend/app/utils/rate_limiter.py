"""Rate limiter for external API calls. Token-bucket and sliding-window implementations."""

import asyncio
import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """
    Async-safe token-bucket rate limiter.

    Usage:
        limiter = RateLimiter(max_calls=50, period_seconds=1.0)
        async with limiter:
            await client.get(url)
    """

    max_calls: int
    period_seconds: float
    _timestamps: list[float] = field(default_factory=list, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def acquire(self) -> None:
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.monotonic()
            # Remove expired timestamps
            cutoff = now - self.period_seconds
            self._timestamps = [t for t in self._timestamps if t > cutoff]

            if len(self._timestamps) >= self.max_calls:
                # Need to wait until the oldest timestamp expires
                wait_time = self._timestamps[0] - cutoff
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

                # Re-clean after sleep
                now = time.monotonic()
                cutoff = now - self.period_seconds
                self._timestamps = [t for t in self._timestamps if t > cutoff]

            self._timestamps.append(time.monotonic())

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


# Pre-configured rate limiters for known APIs
CROSSREF_LIMITER = RateLimiter(max_calls=50, period_seconds=1.0)
OPENALEX_LIMITER = RateLimiter(
    max_calls=10, period_seconds=1.0
)  # ~100k/day → ~1.2/s safe
SEMANTIC_SCHOLAR_LIMITER = RateLimiter(max_calls=100, period_seconds=300.0)
# Background-only limiter: uses at most 40% of S2 quota so foreground requests always get through
SEMANTIC_SCHOLAR_BG_LIMITER = RateLimiter(max_calls=40, period_seconds=300.0)
ARXIV_LIMITER = RateLimiter(max_calls=1, period_seconds=3.0)
UNPAYWALL_LIMITER = RateLimiter(max_calls=10, period_seconds=1.0)
PUBLISHER_LIMITER = RateLimiter(max_calls=1, period_seconds=5.0)
