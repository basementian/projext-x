"""Tests for eBay Account endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.account import AccountEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestUpdateHandlingTime:
    async def test_updates_handling_time(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert "/fulfillment_policy/POL-123" in str(request.url)
            return httpx.Response(200, json={
                "policyId": "POL-123",
                "handlingTime": {"unit": "BUSINESS_DAY", "value": 2},
            })

        http = build_http_client(handler)
        ep = AccountEndpoints(http)
        result = await ep.update_handling_time("POL-123", 2)
        assert result["handlingTime"]["value"] == 2
        await http.close()
