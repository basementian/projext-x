"""Rate limiter with sliding window and exponential backoff for eBay APIs."""

import asyncio
import time
from collections import deque

from flipflow.core.exceptions import EbayRateLimitError


class EbayRateLimiter:
    """Tracks API call volume and implements exponential backoff on 429s.

    eBay allows ~5,000 calls/day. This limiter:
    1. Tracks calls in a sliding window
    2. Provides pre-flight check before making calls
    3. Calculates backoff delay after receiving HTTP 429
    """

    def __init__(
        self,
        daily_limit: int = 5000,
        window_seconds: int = 86400,
        max_backoff_seconds: float = 300.0,
        base_backoff_seconds: float = 1.0,
    ):
        self._daily_limit = daily_limit
        self._window_seconds = window_seconds
        self._max_backoff = max_backoff_seconds
        self._base_backoff = base_backoff_seconds
        self._calls: deque[float] = deque()
        self._consecutive_429s: int = 0

    def record_call(self) -> None:
        """Record that an API call was made."""
        self._prune_old()
        self._calls.append(time.monotonic())

    def record_success(self) -> None:
        """Reset backoff counter on successful response."""
        self._consecutive_429s = 0

    def record_rate_limit(self) -> None:
        """Record a 429 response."""
        self._consecutive_429s += 1

    @property
    def calls_remaining(self) -> int:
        """Approximate remaining calls in the current window."""
        self._prune_old()
        return max(0, self._daily_limit - len(self._calls))

    @property
    def is_throttled(self) -> bool:
        """True if we've hit the daily limit."""
        return self.calls_remaining <= 0

    def get_backoff_delay(self) -> float:
        """Calculate exponential backoff delay based on consecutive 429s."""
        if self._consecutive_429s == 0:
            return 0.0
        delay = self._base_backoff * (2 ** (self._consecutive_429s - 1))
        return min(delay, self._max_backoff)

    async def wait_if_needed(self) -> None:
        """Block if backoff is active or raise if daily limit reached."""
        delay = self.get_backoff_delay()
        if delay > 0:
            await asyncio.sleep(delay)

        if self.is_throttled:
            raise EbayRateLimitError(
                f"Daily API limit of {self._daily_limit} calls reached. "
                f"Resets in ~{self._seconds_until_reset():.0f}s."
            )

    def _prune_old(self) -> None:
        """Remove call timestamps outside the sliding window."""
        cutoff = time.monotonic() - self._window_seconds
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()

    def _seconds_until_reset(self) -> float:
        """Seconds until the oldest call falls out of the window."""
        if not self._calls:
            return 0.0
        return max(0.0, self._calls[0] + self._window_seconds - time.monotonic())
