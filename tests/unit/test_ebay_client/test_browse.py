"""Tests for eBay Browse endpoints."""

import httpx

from flipflow.infrastructure.ebay.endpoints.browse import BrowseEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestSearchItems:
    async def test_searches_with_query(self):
        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            assert "item_summary/search" in url
            assert "q=nike+air+max" in url or "q=nike%20air%20max" in url or "q=nike+air+max" in url
            # Verify app token is used (checked via header in build_http_client)
            assert request.headers["Authorization"] == "Bearer test-app-token"
            return httpx.Response(
                200,
                json={
                    "itemSummaries": [{"itemId": "I-1", "title": "Nike Air Max"}],
                    "total": 1,
                },
            )

        http = build_http_client(handler)
        ep = BrowseEndpoints(http)
        result = await ep.search_items("nike air max")
        assert result["total"] == 1
        assert result["itemSummaries"][0]["title"] == "Nike Air Max"
        await http.close()

    async def test_search_with_filters(self):
        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            assert "filter=" in url
            return httpx.Response(200, json={"itemSummaries": [], "total": 0})

        http = build_http_client(handler)
        ep = BrowseEndpoints(http)
        result = await ep.search_items("test", filters={"categoryId": "12345"})
        assert result["total"] == 0
        await http.close()
