"""eBay Sell Marketing API endpoints."""

from flipflow.core.exceptions import EbayNotFoundError
from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class MarketingEndpoints:
    """Maps EbayGateway marketing methods to eBay REST API calls."""

    BASE = "/sell/marketing/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def create_campaign(self, campaign_data: dict) -> dict:
        """POST /sell/marketing/v1/ad_campaign"""
        response = await self._http.post(
            f"{self.BASE}/ad_campaign",
            json=campaign_data,
        )
        campaign_id = ""
        location = response.headers.get("Location", "")
        if location:
            campaign_id = location.rstrip("/").rsplit("/", 1)[-1]
        result = response.json() if response.status_code != 201 else {}
        result["campaignId"] = campaign_id or result.get("campaignId", "")
        return result

    async def end_campaign(self, campaign_id: str) -> bool:
        """POST /sell/marketing/v1/ad_campaign/{campaignId}/end"""
        try:
            await self._http.post(
                f"{self.BASE}/ad_campaign/{campaign_id}/end",
            )
            return True
        except EbayNotFoundError:
            return False

    async def get_campaign(self, campaign_id: str) -> dict | None:
        """GET /sell/marketing/v1/ad_campaign/{campaignId}"""
        try:
            response = await self._http.get(
                f"{self.BASE}/ad_campaign/{campaign_id}",
            )
            return response.json()
        except EbayNotFoundError:
            return None
