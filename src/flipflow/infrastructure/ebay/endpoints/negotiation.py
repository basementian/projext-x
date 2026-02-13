"""eBay Sell Negotiation API endpoints."""

from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class NegotiationEndpoints:
    """Maps EbayGateway buyer engagement methods to eBay REST API calls."""

    BASE = "/sell/negotiation/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def send_offer_to_buyer(
        self, listing_id: str, buyer_id: str, offer_data: dict,
    ) -> dict:
        """POST /sell/negotiation/v1/send_offer_to_interested_buyers"""
        payload = {
            "offeredItems": [
                {
                    "listingId": listing_id,
                    "price": {
                        "currency": offer_data.get("currency", "USD"),
                        "value": str(offer_data.get("price", "")),
                    },
                }
            ],
            "message": offer_data.get("message", ""),
        }
        response = await self._http.post(
            f"{self.BASE}/send_offer_to_interested_buyers", json=payload,
        )
        return response.json()

    async def get_watchers(self, listing_id: str) -> list[dict]:
        """GET /sell/negotiation/v1/find_eligible_items

        Filters findEligibleItems response to the requested listing.
        """
        response = await self._http.get(
            f"{self.BASE}/find_eligible_items", params={"limit": 100},
        )
        data = response.json()
        eligible = data.get("eligibleItems", [])

        watchers = []
        for item in eligible:
            if item.get("listingId") == listing_id:
                for buyer in item.get("interestedBuyers", []):
                    watchers.append({
                        "buyerId": buyer.get("buyerId", ""),
                        "watchDate": buyer.get("addedDate", ""),
                    })
        return watchers

    async def respond_to_offer(
        self, listing_id: str, offer_id: str, action: str, counter_amount: float | None = None,
    ) -> dict:
        """POST /sell/negotiation/v1/respond_to_offer

        Actions: accept, counter, reject.
        """
        payload = {
            "offerId": offer_id,
            "action": action.upper(),
        }
        if counter_amount is not None:
            payload["counterOffer"] = {
                "price": {"currency": "USD", "value": str(counter_amount)},
            }
        response = await self._http.post(
            f"{self.BASE}/respond_to_offer", json=payload,
        )
        return response.json()
