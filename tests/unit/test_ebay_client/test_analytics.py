"""Tests for eBay Analytics endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.analytics import AnalyticsEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestGetTrafficReport:
    async def test_returns_traffic_data(self):
        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            assert "traffic_report" in url
            assert "dimension=LISTING" in url
            return httpx.Response(200, json={
                "records": [
                    {"listingId": "123", "views": 42, "impressions": 500},
                ],
            })

        http = build_http_client(handler)
        ep = AnalyticsEndpoints(http)
        result = await ep.get_traffic_report(
            listing_ids=["123"],
            date_range="[2026-01-01..2026-01-31]",
            metrics=["LISTING_VIEWS_TOTAL", "LISTING_IMPRESSIONS_TOTAL"],
        )
        assert len(result["records"]) == 1
        assert result["records"][0]["views"] == 42
        await http.close()
