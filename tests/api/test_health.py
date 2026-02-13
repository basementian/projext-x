"""API tests for health endpoint."""

from httpx import ASGITransport, AsyncClient

from flipflow.api.app import create_app
from flipflow.core.config import FlipFlowConfig


class TestHealth:

    async def test_health_endpoint(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "flipflow"
        assert data["version"] == "0.1.0"


    async def test_trusted_host_blocks_unlisted_hosts(self):
        config = FlipFlowConfig(
            database_url="sqlite+aiosqlite:///:memory:",
            ebay_mode="mock",
            allowed_hosts=["api.flipflow.local"],
            _env_file=None,
        )
        app = create_app(config)

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://malicious.local",
        ) as client:
            response = await client.get("/api/v1/health")

        assert response.status_code == 400
