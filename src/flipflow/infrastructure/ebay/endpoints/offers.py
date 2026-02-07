"""eBay Sell Inventory API — Offer endpoints."""

from flipflow.core.exceptions import EbayNotFoundError
from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class OfferEndpoints:
    """Maps EbayGateway offer methods to eBay REST API calls."""

    BASE = "/sell/inventory/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def create_offer(self, offer_data: dict) -> dict:
        """POST /sell/inventory/v1/offer"""
        response = await self._http.post(f"{self.BASE}/offer", json=offer_data)
        return response.json()

    async def publish_offer(self, offer_id: str) -> dict:
        """POST /sell/inventory/v1/offer/{offerId}/publish"""
        response = await self._http.post(
            f"{self.BASE}/offer/{offer_id}/publish",
        )
        return response.json()

    async def withdraw_offer(self, offer_id: str) -> dict:
        """POST /sell/inventory/v1/offer/{offerId}/withdraw"""
        response = await self._http.post(
            f"{self.BASE}/offer/{offer_id}/withdraw",
        )
        return response.json()

    async def get_offer(self, offer_id: str) -> dict | None:
        """GET /sell/inventory/v1/offer/{offerId}"""
        try:
            response = await self._http.get(f"{self.BASE}/offer/{offer_id}")
            return response.json()
        except EbayNotFoundError:
            return None

    async def get_offers_by_sku(self, sku: str) -> list[dict]:
        """GET /sell/inventory/v1/offer?sku={sku}"""
        response = await self._http.get(
            f"{self.BASE}/offer",
            params={"sku": sku, "format": "FIXED_PRICE"},
        )
        data = response.json()
        return data.get("offers", [])
