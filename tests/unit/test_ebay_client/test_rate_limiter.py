"""Tests for eBay rate limiter."""

import time

import pytest

from flipflow.core.exceptions import EbayRateLimitError
from flipflow.infrastructure.ebay.rate_limiter import EbayRateLimiter


class TestCallTracking:
    def test_fresh_limiter_has_full_quota(self):
        limiter = EbayRateLimiter(daily_limit=5000)
        assert limiter.calls_remaining == 5000

    def test_record_call_decrements(self):
        limiter = EbayRateLimiter(daily_limit=100)
        limiter.record_call()
        assert limiter.calls_remaining == 99

    def test_multiple_calls(self):
        limiter = EbayRateLimiter(daily_limit=100)
        for _ in range(10):
            limiter.record_call()
        assert limiter.calls_remaining == 90

    def test_is_throttled_at_limit(self):
        limiter = EbayRateLimiter(daily_limit=3)
        assert limiter.is_throttled is False
        limiter.record_call()
        limiter.record_call()
        limiter.record_call()
        assert limiter.is_throttled is True

    def test_not_throttled_below_limit(self):
        limiter = EbayRateLimiter(daily_limit=100)
        limiter.record_call()
        assert limiter.is_throttled is False


class TestBackoff:
    def test_no_backoff_initially(self):
        limiter = EbayRateLimiter()
        assert limiter.get_backoff_delay() == 0.0

    def test_first_429_gives_base_backoff(self):
        limiter = EbayRateLimiter(base_backoff_seconds=1.0)
        limiter.record_rate_limit()
        assert limiter.get_backoff_delay() == 1.0

    def test_exponential_progression(self):
        limiter = EbayRateLimiter(base_backoff_seconds=1.0)
        limiter.record_rate_limit()  # 1s
        assert limiter.get_backoff_delay() == 1.0
        limiter.record_rate_limit()  # 2s
        assert limiter.get_backoff_delay() == 2.0
        limiter.record_rate_limit()  # 4s
        assert limiter.get_backoff_delay() == 4.0
        limiter.record_rate_limit()  # 8s
        assert limiter.get_backoff_delay() == 8.0

    def test_backoff_capped_at_max(self):
        limiter = EbayRateLimiter(base_backoff_seconds=1.0, max_backoff_seconds=5.0)
        for _ in range(10):
            limiter.record_rate_limit()
        assert limiter.get_backoff_delay() == 5.0

    def test_success_resets_backoff(self):
        limiter = EbayRateLimiter(base_backoff_seconds=1.0)
        limiter.record_rate_limit()
        limiter.record_rate_limit()
        assert limiter.get_backoff_delay() == 2.0
        limiter.record_success()
        assert limiter.get_backoff_delay() == 0.0


class TestWaitIfNeeded:
    async def test_raises_when_throttled(self):
        limiter = EbayRateLimiter(daily_limit=1)
        limiter.record_call()
        with pytest.raises(EbayRateLimitError, match="Daily API limit"):
            await limiter.wait_if_needed()

    async def test_no_error_when_not_throttled(self):
        limiter = EbayRateLimiter(daily_limit=100)
        await limiter.wait_if_needed()  # Should not raise


class TestSlidingWindow:
    def test_old_calls_pruned(self):
        limiter = EbayRateLimiter(daily_limit=100, window_seconds=1)
        limiter.record_call()
        assert limiter.calls_remaining == 99
        # Manually age the call
        limiter._calls[0] = time.monotonic() - 2
        assert limiter.calls_remaining == 100
