"""API tests for authentication middleware."""

from httpx import ASGITransport, AsyncClient


class TestApiKeyAuth:
    async def test_health_is_public(self, app):
        """Health endpoint should work without API key."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200

    async def test_protected_endpoint_requires_key(self, app):
        """Listings endpoint should reject requests without API key."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/api/v1/listings")
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]

    async def test_wrong_key_rejected(self, app):
        """Wrong API key should be rejected."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"X-API-Key": "wrong-key"},
        ) as c:
            response = await c.get("/api/v1/listings")
        assert response.status_code == 401

    async def test_valid_key_accepted(self, client):
        """Valid API key should pass through."""
        response = await client.get("/api/v1/listings")
        assert response.status_code == 200

    async def test_no_auth_mode(self, client_no_auth):
        """When api_key is empty, all endpoints are open."""
        response = await client_no_auth.get("/api/v1/listings")
        assert response.status_code == 200
