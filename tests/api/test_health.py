"""API tests for health endpoint."""


class TestHealth:
    async def test_health_endpoint(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "flipflow"
        assert data["version"] == "0.1.0"
        assert data["database"] == "connected"

    async def test_health_is_public(self, app):
        """Health check works without auth (already tested in test_auth, but explicit)."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as c:
            response = await c.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["database"] == "connected"
