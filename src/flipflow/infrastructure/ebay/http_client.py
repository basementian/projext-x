"""Base HTTP client for eBay REST APIs with auth, retry, and rate limiting."""

import logging
from typing import Any

import httpx

from flipflow.core.exceptions import (
    EbayAuthError,
    EbayError,
    EbayNotFoundError,
    EbayRateLimitError,
)
from flipflow.infrastructure.ebay.rate_limiter import EbayRateLimiter
from flipflow.infrastructure.ebay.token_manager import EbayTokenManager

logger = logging.getLogger(__name__)

BASE_URLS = {
    "production": "https://api.ebay.com",
    "sandbox": "https://api.sandbox.ebay.com",
}

MAX_RETRIES = 3


class EbayHttpClient:
    """Authenticated httpx client for eBay REST APIs.

    Features:
    - Automatic Bearer token injection (user or app token)
    - Rate limit tracking with exponential backoff on 429
    - Retry on transient errors (429, 500, 502, 503)
    - Maps HTTP errors to FlipFlow exception hierarchy
    """

    RETRYABLE_STATUS_CODES = {429, 500, 502, 503}

    def __init__(
        self,
        token_manager: EbayTokenManager,
        rate_limiter: EbayRateLimiter,
        mode: str = "sandbox",
    ):
        self._token_manager = token_manager
        self._rate_limiter = rate_limiter
        self._mode = mode
        base_url = BASE_URLS.get(mode, BASE_URLS["sandbox"])
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(30.0, connect=10.0),
            headers={"Accept": "application/json"},
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict | list | None = None,
        params: dict[str, Any] | None = None,
        data: dict | None = None,
        use_app_token: bool = False,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Make an authenticated request with retry and rate limiting."""
        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES):
            await self._rate_limiter.wait_if_needed()

            if use_app_token:
                token = await self._token_manager.get_app_token()
            else:
                token = await self._token_manager.get_user_token()

            request_headers = {
                "Authorization": f"Bearer {token}",
                "Content-Language": "en-US",
            }
            if headers:
                request_headers.update(headers)

            self._rate_limiter.record_call()

            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                    data=data,
                    headers=request_headers,
                )
            except httpx.TimeoutException as exc:
                last_error = EbayError(f"Request timed out: {exc}")
                logger.warning(
                    "eBay timeout (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    path,
                )
                continue
            except httpx.HTTPError as exc:
                last_error = EbayError(f"HTTP transport error: {exc}")
                logger.warning(
                    "eBay transport error (attempt %d/%d): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                continue

            if response.status_code in self.RETRYABLE_STATUS_CODES:
                if response.status_code == 429:
                    self._rate_limiter.record_rate_limit()
                    logger.warning(
                        "eBay 429 (attempt %d/%d)",
                        attempt + 1,
                        MAX_RETRIES,
                    )
                else:
                    logger.warning(
                        "eBay %d (attempt %d/%d): %s",
                        response.status_code,
                        attempt + 1,
                        MAX_RETRIES,
                        path,
                    )
                last_error = self._map_error(response)
                continue

            if response.status_code >= 400:
                raise self._map_error(response)

            self._rate_limiter.record_success()
            return response

        raise last_error or EbayError("Request failed after all retries")

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    def _map_error(self, response: httpx.Response) -> EbayError:
        """Map HTTP status codes to FlipFlow exception hierarchy."""
        status = response.status_code
        try:
            body = response.json()
            message = body.get("errors", [{}])[0].get("message", response.text)
        except Exception:
            message = response.text

        if status in (401, 403):
            return EbayAuthError(f"Authentication failed ({status}): {message}")
        if status == 404:
            return EbayNotFoundError(f"Resource not found: {message}")
        if status == 429:
            return EbayRateLimitError(f"Rate limit exceeded: {message}")
        return EbayError(f"eBay API error ({status}): {message}")

    async def close(self) -> None:
        """Close the underlying httpx client and token manager."""
        await self._client.aclose()
        await self._token_manager.close()
