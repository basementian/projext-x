"""eBay Sell Account API endpoints."""

from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class AccountEndpoints:
    """Maps EbayGateway account methods to eBay REST API calls."""

    BASE = "/sell/account/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def update_handling_time(self, policy_id: str, handling_days: int) -> dict:
        """PUT /sell/account/v1/fulfillment_policy/{fulfillment_policy_id}"""
        payload = {
            "handlingTime": {
                "unit": "BUSINESS_DAY",
                "value": handling_days,
            },
        }
        response = await self._http.put(
            f"{self.BASE}/fulfillment_policy/{policy_id}",
            json=payload,
        )
        return response.json()
