"""Tests for eBay Marketing endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.marketing import MarketingEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestCreateCampaign:
    async def test_extracts_campaign_id_from_location(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/ad_campaign" in str(request.url)
            return httpx.Response(
                201,
                headers={"Location": "/sell/marketing/v1/ad_campaign/CAMP-ABC"},
            )

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        result = await ep.create_campaign({"campaignName": "Test"})
        assert result["campaignId"] == "CAMP-ABC"
        await http.close()

    async def test_fallback_to_json_campaign_id(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"campaignId": "CAMP-FROM-JSON"})

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        result = await ep.create_campaign({"campaignName": "Test"})
        assert result["campaignId"] == "CAMP-FROM-JSON"
        await http.close()


class TestEndCampaign:
    async def test_ends_campaign(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "/ad_campaign/CAMP-123/end" in str(request.url)
            return httpx.Response(204)

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        assert await ep.end_campaign("CAMP-123") is True
        await http.close()

    async def test_returns_false_on_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"errors": [{"message": "Not found"}]})

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        assert await ep.end_campaign("MISSING") is False
        await http.close()


class TestGetCampaign:
    async def test_returns_campaign(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"campaignId": "CAMP-123", "status": "RUNNING"})

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        result = await ep.get_campaign("CAMP-123")
        assert result["status"] == "RUNNING"
        await http.close()

    async def test_returns_none_on_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"errors": [{"message": "Not found"}]})

        http = build_http_client(handler)
        ep = MarketingEndpoints(http)
        assert await ep.get_campaign("MISSING") is None
        await http.close()
