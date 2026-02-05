"""API tests for health endpoint."""


class TestHealth:
    async def test_health_endpoint(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "flipflow"
        assert data["version"] == "0.1.0"
