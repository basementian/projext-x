"""Shared fixtures for real eBay client tests."""

import time

import httpx
import pytest

from flipflow.core.config import FlipFlowConfig
from flipflow.infrastructure.ebay.http_client import EbayHttpClient
from flipflow.infrastructure.ebay.rate_limiter import EbayRateLimiter
from flipflow.infrastructure.ebay.token_manager import EbayTokenManager, TokenData


def make_token_response(
    access_token="mock-token-123", expires_in=7200, status=200,
):
    """Build a valid eBay token response body."""
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "scope": "https://api.ebay.com/oauth/api_scope",
    }


def build_http_client(handler) -> EbayHttpClient:
    """Build an EbayHttpClient with a mock transport for testing.

    Pre-seeds tokens so endpoint tests don't need to mock the token endpoint.
    """
    token_mgr = EbayTokenManager(
        client_id="test-id",
        client_secret="test-secret",
        refresh_token="test-refresh",
        base_url="https://api.sandbox.ebay.com",
    )
    token_mgr._user_token = TokenData(
        access_token="test-bearer-token",
        token_type="Bearer",
        expires_at=time.monotonic() + 7200,
    )
    token_mgr._app_token = TokenData(
        access_token="test-app-token",
        token_type="Bearer",
        expires_at=time.monotonic() + 7200,
    )

    rate_limiter = EbayRateLimiter()
    http = EbayHttpClient(
        token_manager=token_mgr,
        rate_limiter=rate_limiter,
        mode="sandbox",
    )
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.sandbox.ebay.com",
    )
    return http


@pytest.fixture
def sandbox_config():
    """Config for sandbox mode testing."""
    return FlipFlowConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        ebay_mode="sandbox",
        ebay_client_id="test-client-id",
        ebay_client_secret="test-client-secret",
        ebay_redirect_uri="https://localhost/callback",
        ebay_refresh_token="test-refresh-token",
    )
