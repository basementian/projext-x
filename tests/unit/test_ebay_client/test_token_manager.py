"""Tests for eBay OAuth token manager."""

import time

import httpx
import pytest

from flipflow.core.exceptions import EbayAuthError
from flipflow.infrastructure.ebay.token_manager import (
    EbayTokenManager,
    TokenData,
)
from tests.unit.test_ebay_client.conftest import make_token_response


def _make_manager(handler) -> EbayTokenManager:
    """Build a token manager with mock HTTP transport."""
    mgr = EbayTokenManager(
        client_id="test-id",
        client_secret="test-secret",
        refresh_token="test-refresh",
        base_url="https://api.sandbox.ebay.com",
    )
    mgr._http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.sandbox.ebay.com",
        auth=("test-id", "test-secret"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return mgr


class TestTokenData:
    def test_not_expired_when_fresh(self):
        token = TokenData(
            access_token="abc",
            token_type="Bearer",
            expires_at=time.monotonic() + 7200,
        )
        assert token.is_expired is False

    def test_expired_when_past(self):
        token = TokenData(
            access_token="abc",
            token_type="Bearer",
            expires_at=time.monotonic() - 1,
        )
        assert token.is_expired is True

    def test_expired_within_buffer(self):
        # Within 5-minute buffer
        token = TokenData(
            access_token="abc",
            token_type="Bearer",
            expires_at=time.monotonic() + 200,  # Less than 300s buffer
        )
        assert token.is_expired is True

    def test_not_expired_outside_buffer(self):
        token = TokenData(
            access_token="abc",
            token_type="Bearer",
            expires_at=time.monotonic() + 400,  # More than 300s buffer
        )
        assert token.is_expired is False


class TestUserToken:
    async def test_fetches_user_token(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert b"grant_type=refresh_token" in request.content
            assert b"refresh_token=test-refresh" in request.content
            return httpx.Response(200, json=make_token_response("user-tok-123"))

        mgr = _make_manager(handler)
        token = await mgr.get_user_token()
        assert token == "user-tok-123"
        await mgr.close()

    async def test_caches_token(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json=make_token_response("cached-tok"))

        mgr = _make_manager(handler)
        await mgr.get_user_token()
        await mgr.get_user_token()
        assert call_count == 1  # Only one HTTP call
        await mgr.close()

    async def test_refreshes_expired_token(self):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json=make_token_response(f"tok-{call_count}"))

        mgr = _make_manager(handler)
        await mgr.get_user_token()
        # Expire the cached token
        mgr._user_token.expires_at = time.monotonic() - 1
        token = await mgr.get_user_token()
        assert call_count == 2
        assert token == "tok-2"
        await mgr.close()

    async def test_auth_error_on_failure(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, text="Invalid credentials")

        mgr = _make_manager(handler)
        with pytest.raises(EbayAuthError, match="Token request failed"):
            await mgr.get_user_token()
        await mgr.close()


class TestAppToken:
    async def test_fetches_app_token(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert b"grant_type=client_credentials" in request.content
            return httpx.Response(200, json=make_token_response("app-tok-456"))

        mgr = _make_manager(handler)
        token = await mgr.get_app_token()
        assert token == "app-tok-456"
        await mgr.close()

    async def test_user_and_app_tokens_independent(self):
        def handler(request: httpx.Request) -> httpx.Response:
            if b"refresh_token" in request.content:
                return httpx.Response(200, json=make_token_response("user-tok"))
            return httpx.Response(200, json=make_token_response("app-tok"))

        mgr = _make_manager(handler)
        user = await mgr.get_user_token()
        app = await mgr.get_app_token()
        assert user == "user-tok"
        assert app == "app-tok"
        await mgr.close()


class TestClose:
    async def test_close_cleans_up(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json=make_token_response())

        mgr = _make_manager(handler)
        await mgr.get_user_token()
        await mgr.close()
        assert mgr._http is None
