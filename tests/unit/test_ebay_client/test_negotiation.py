"""Tests for eBay Negotiation endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.negotiation import NegotiationEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestSendOfferToBuyer:
    async def test_sends_offer(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "send_offer_to_interested_buyers" in str(request.url)
            assert request.method == "POST"
            return httpx.Response(200, json={"status": "SENT"})

        http = build_http_client(handler)
        ep = NegotiationEndpoints(http)
        result = await ep.send_offer_to_buyer(
            "LISTING-123",
            "BUYER-456",
            {"price": 45.0, "currency": "USD", "message": "Special deal!"},
        )
        assert result["status"] == "SENT"
        await http.close()


class TestGetWatchers:
    async def test_returns_watchers_for_listing(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert "find_eligible_items" in str(request.url)
            return httpx.Response(
                200,
                json={
                    "eligibleItems": [
                        {
                            "listingId": "LISTING-123",
                            "interestedBuyers": [
                                {"buyerId": "B-1", "addedDate": "2026-01-20"},
                                {"buyerId": "B-2", "addedDate": "2026-01-21"},
                            ],
                        },
                        {
                            "listingId": "OTHER-999",
                            "interestedBuyers": [
                                {"buyerId": "B-3"},
                            ],
                        },
                    ],
                },
            )

        http = build_http_client(handler)
        ep = NegotiationEndpoints(http)
        watchers = await ep.get_watchers("LISTING-123")
        assert len(watchers) == 2
        assert watchers[0]["buyerId"] == "B-1"
        assert watchers[1]["buyerId"] == "B-2"
        await http.close()

    async def test_returns_empty_for_no_matches(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"eligibleItems": []})

        http = build_http_client(handler)
        ep = NegotiationEndpoints(http)
        watchers = await ep.get_watchers("LISTING-123")
        assert watchers == []
        await http.close()
