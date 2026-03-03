"""Token-bucket rate limiter with jittered delays."""

import asyncio
import random
import time

from src.scrapers.config import (
    DEFAULT_MAX_DELAY_SEC,
    DEFAULT_MIN_DELAY_SEC,
    MAX_REQUESTS_PER_MINUTE,
    TOKEN_BUCKET_CAPACITY,
)


class RateLimiter:
    """Token-bucket rate limiter for respectful web scraping.

    Enforces both per-request jittered delays and an overall
    requests-per-minute cap using a token bucket algorithm.
    """

    def __init__(
        self,
        min_delay: float = DEFAULT_MIN_DELAY_SEC,
        max_delay: float = DEFAULT_MAX_DELAY_SEC,
        rpm: int = MAX_REQUESTS_PER_MINUTE,
        capacity: int = TOKEN_BUCKET_CAPACITY,
    ) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._rpm = rpm
        self._capacity = capacity

        # Token bucket state
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._refill_rate = rpm / 60.0  # tokens per second
        self._request_count = 0

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._capacity,
            self._tokens + elapsed * self._refill_rate,
        )
        self._last_refill = now

    async def acquire(self) -> float:
        """Wait until a request is allowed. Returns the delay waited (seconds)."""
        total_delay = 0.0

        # Wait for a token
        while True:
            self._refill()
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                break
            wait = (1.0 - self._tokens) / self._refill_rate
            await asyncio.sleep(wait)
            total_delay += wait

        # Add jittered delay between requests
        jitter = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(jitter)
        total_delay += jitter

        self._request_count += 1
        return total_delay

    @property
    def request_count(self) -> int:
        """Total requests made through this limiter."""
        return self._request_count

    def reset(self) -> None:
        """Reset the limiter state."""
        self._tokens = float(self._capacity)
        self._last_refill = time.monotonic()
        self._request_count = 0
