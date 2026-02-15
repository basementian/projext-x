"""Tests for eBay base HTTP client."""

import time

import httpx
import pytest

from flipflow.core.exceptions import (
    EbayAuthError,
    EbayError,
    EbayNotFoundError,
)
from flipflow.infrastructure.ebay.http_client import BASE_URLS, EbayHttpClient
from flipflow.infrastructure.ebay.rate_limiter import EbayRateLimiter
from flipflow.infrastructure.ebay.token_manager import EbayTokenManager, TokenData


def _build_client(handler, mode="sandbox") -> EbayHttpClient:
    """Build an HTTP client with mock transport and pre-seeded tokens."""
    token_mgr = EbayTokenManager(
        client_id="test-id",
        client_secret="test-secret",
        refresh_token="test-refresh",
        base_url="https://api.sandbox.ebay.com",
    )
    token_mgr._user_token = TokenData(
        access_token="user-bearer",
        token_type="Bearer",
        expires_at=time.monotonic() + 7200,
    )
    token_mgr._app_token = TokenData(
        access_token="app-bearer",
        token_type="Bearer",
        expires_at=time.monotonic() + 7200,
    )

    rate_limiter = EbayRateLimiter()
    http = EbayHttpClient(
        token_manager=token_mgr,
        rate_limiter=rate_limiter,
        mode=mode,
    )
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=BASE_URLS.get(mode, BASE_URLS["sandbox"]),
    )
    return http


class TestAuthHeaders:
    async def test_injects_bearer_token(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer user-bearer"
            return httpx.Response(200, json={"ok": True})

        client = _build_client(handler)
        response = await client.get("/test")
        assert response.status_code == 200
        await client.close()

    async def test_uses_app_token_when_flagged(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["Authorization"] == "Bearer app-bearer"
            return httpx.Response(200, json={"ok": True})

        client = _build_client(handler)
        await client.get("/test", use_app_token=True)
        await client.close()


class TestRetry:
    async def test_retries_on_500(self):
        attempts = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                return httpx.Response(500, text="Server error")
            return httpx.Response(200, json={"ok": True})

        client = _build_client(handler)
        response = await client.get("/test")
        assert response.status_code == 200
        assert attempts == 3
        await client.close()

    async def test_retries_on_429(self):
        attempts = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                return httpx.Response(429, text="Rate limited")
            return httpx.Response(200, json={"ok": True})

        client = _build_client(handler)
        response = await client.get("/test")
        assert response.status_code == 200
        await client.close()

    async def test_raises_after_all_retries_exhausted(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Persistent error")

        client = _build_client(handler)
        with pytest.raises(EbayError, match="eBay API error"):
            await client.get("/test")
        await client.close()


class TestErrorMapping:
    async def test_404_raises_not_found(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                404,
                json={"errors": [{"message": "Item not found"}]},
            )

        client = _build_client(handler)
        with pytest.raises(EbayNotFoundError, match="Item not found"):
            await client.get("/test")
        await client.close()

    async def test_401_raises_auth_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401,
                json={"errors": [{"message": "Invalid token"}]},
            )

        client = _build_client(handler)
        with pytest.raises(EbayAuthError, match="Invalid token"):
            await client.get("/test")
        await client.close()

    async def test_403_raises_auth_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(403, text="Forbidden")

        client = _build_client(handler)
        with pytest.raises(EbayAuthError, match="Authentication failed"):
            await client.get("/test")
        await client.close()


class TestBaseUrls:
    def test_sandbox_url(self):
        assert BASE_URLS["sandbox"] == "https://api.sandbox.ebay.com"

    def test_production_url(self):
        assert BASE_URLS["production"] == "https://api.ebay.com"
