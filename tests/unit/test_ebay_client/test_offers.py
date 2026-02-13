"""Tests for eBay Offer endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.offers import OfferEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestCreateOffer:
    async def test_creates_offer(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "/offer" in str(request.url)
            return httpx.Response(201, json={"offerId": "OFF-123"})

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        result = await ep.create_offer({"sku": "SKU-001"})
        assert result["offerId"] == "OFF-123"
        await http.close()


class TestPublishOffer:
    async def test_publishes_offer(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "/offer/OFF-123/publish" in str(request.url)
            return httpx.Response(200, json={"listingId": "EBAY-999"})

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        result = await ep.publish_offer("OFF-123")
        assert result["listingId"] == "EBAY-999"
        await http.close()


class TestWithdrawOffer:
    async def test_withdraws_offer(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "/offer/OFF-123/withdraw" in str(request.url)
            return httpx.Response(200, json={"offerId": "OFF-123", "status": "WITHDRAWN"})

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        result = await ep.withdraw_offer("OFF-123")
        assert result["status"] == "WITHDRAWN"
        await http.close()


class TestGetOffer:
    async def test_returns_offer(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"offerId": "OFF-123", "sku": "SKU-001"})

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        result = await ep.get_offer("OFF-123")
        assert result["offerId"] == "OFF-123"
        await http.close()

    async def test_returns_none_on_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"errors": [{"message": "Not found"}]})

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        assert await ep.get_offer("MISSING") is None
        await http.close()


class TestGetOffersBySku:
    async def test_returns_offers_list(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "sku=SKU-001" in str(request.url)
            return httpx.Response(200, json={
                "offers": [{"offerId": "OFF-1"}, {"offerId": "OFF-2"}],
            })

        http = build_http_client(handler)
        ep = OfferEndpoints(http)
        result = await ep.get_offers_by_sku("SKU-001")
        assert len(result) == 2
        await http.close()
