"""eBay Buy Browse API endpoints."""

from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class BrowseEndpoints:
    """Maps EbayGateway browse methods to eBay REST API calls.

    Note: Browse API uses Application token (not User token).
    """

    BASE = "/buy/browse/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def search_items(self, query: str, filters: dict | None = None) -> dict:
        """GET /buy/browse/v1/item_summary/search"""
        params: dict = {"q": query, "limit": 50}
        if filters:
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f"{key}:{{{value}}}")
            if filter_parts:
                params["filter"] = ",".join(filter_parts)

        response = await self._http.get(
            f"{self.BASE}/item_summary/search",
            params=params,
            use_app_token=True,
        )
        return response.json()
