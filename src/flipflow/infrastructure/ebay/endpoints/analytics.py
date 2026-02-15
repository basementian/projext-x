"""eBay Sell Analytics API endpoints."""

from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class AnalyticsEndpoints:
    """Maps EbayGateway analytics methods to eBay REST API calls."""

    BASE = "/sell/analytics/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def get_traffic_report(
        self,
        listing_ids: list[str],
        date_range: str,
        metrics: list[str],
    ) -> dict:
        """GET /sell/analytics/v1/traffic_report"""
        params = {
            "dimension": "LISTING",
            "filter": (f"listing_ids:{{{','.join(listing_ids)}}};" f"date_range:{date_range}"),
            "metric": ",".join(metrics),
        }
        response = await self._http.get(
            f"{self.BASE}/traffic_report",
            params=params,
        )
        return response.json()
