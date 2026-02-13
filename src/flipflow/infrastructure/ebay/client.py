"""Real eBay client — implements EbayGateway using live eBay REST APIs."""

from flipflow.core.config import FlipFlowConfig
from flipflow.infrastructure.ebay.http_client import EbayHttpClient
from flipflow.infrastructure.ebay.rate_limiter import EbayRateLimiter
from flipflow.infrastructure.ebay.token_manager import EbayTokenManager
from flipflow.infrastructure.ebay.endpoints.inventory import InventoryEndpoints
from flipflow.infrastructure.ebay.endpoints.offers import OfferEndpoints
from flipflow.infrastructure.ebay.endpoints.analytics import AnalyticsEndpoints
from flipflow.infrastructure.ebay.endpoints.marketing import MarketingEndpoints
from flipflow.infrastructure.ebay.endpoints.browse import BrowseEndpoints
from flipflow.infrastructure.ebay.endpoints.negotiation import NegotiationEndpoints
from flipflow.infrastructure.ebay.endpoints.account import AccountEndpoints


class RealEbayClient:
    """Production implementation of the EbayGateway protocol.

    Composes endpoint modules over a shared HTTP client with
    automatic token management and rate limiting.
    """

    def __init__(self, config: FlipFlowConfig):
        base_url = (
            "https://api.ebay.com" if config.ebay_mode == "production"
            else "https://api.sandbox.ebay.com"
        )
        self._token_manager = EbayTokenManager(
            client_id=config.ebay_client_id,
            client_secret=config.ebay_client_secret,
            refresh_token=config.ebay_refresh_token,
            base_url=base_url,
        )
        self._rate_limiter = EbayRateLimiter()
        self._http = EbayHttpClient(
            token_manager=self._token_manager,
            rate_limiter=self._rate_limiter,
            mode=config.ebay_mode,
        )

        self._inventory = InventoryEndpoints(self._http)
        self._offers = OfferEndpoints(self._http)
        self._analytics = AnalyticsEndpoints(self._http)
        self._marketing = MarketingEndpoints(self._http)
        self._browse = BrowseEndpoints(self._http)
        self._negotiation = NegotiationEndpoints(self._http)
        self._account = AccountEndpoints(self._http)

    # === Inventory Management ===

    async def create_inventory_item(self, sku: str, item_data: dict) -> dict:
        return await self._inventory.create_inventory_item(sku, item_data)

    async def get_inventory_item(self, sku: str) -> dict | None:
        return await self._inventory.get_inventory_item(sku)

    async def update_inventory_item(self, sku: str, item_data: dict) -> dict:
        return await self._inventory.update_inventory_item(sku, item_data)

    async def delete_inventory_item(self, sku: str) -> bool:
        return await self._inventory.delete_inventory_item(sku)

    async def bulk_update_price_quantity(self, updates: list[dict]) -> dict:
        return await self._inventory.bulk_update_price_quantity(updates)

    # === Offer Management ===

    async def create_offer(self, offer_data: dict) -> dict:
        return await self._offers.create_offer(offer_data)

    async def publish_offer(self, offer_id: str) -> dict:
        return await self._offers.publish_offer(offer_id)

    async def withdraw_offer(self, offer_id: str) -> dict:
        return await self._offers.withdraw_offer(offer_id)

    async def get_offer(self, offer_id: str) -> dict | None:
        return await self._offers.get_offer(offer_id)

    async def get_offers_by_sku(self, sku: str) -> list[dict]:
        return await self._offers.get_offers_by_sku(sku)

    # === Analytics ===

    async def get_traffic_report(
        self, listing_ids: list[str], date_range: str, metrics: list[str],
    ) -> dict:
        return await self._analytics.get_traffic_report(
            listing_ids, date_range, metrics,
        )

    # === Marketing ===

    async def create_campaign(self, campaign_data: dict) -> dict:
        return await self._marketing.create_campaign(campaign_data)

    async def end_campaign(self, campaign_id: str) -> bool:
        return await self._marketing.end_campaign(campaign_id)

    async def get_campaign(self, campaign_id: str) -> dict | None:
        return await self._marketing.get_campaign(campaign_id)

    # === Browse ===

    async def search_items(self, query: str, filters: dict | None = None) -> dict:
        return await self._browse.search_items(query, filters)

    # === Buyer Engagement ===

    async def send_offer_to_buyer(
        self, listing_id: str, buyer_id: str, offer_data: dict,
    ) -> dict:
        return await self._negotiation.send_offer_to_buyer(
            listing_id, buyer_id, offer_data,
        )

    async def get_watchers(self, listing_id: str) -> list[dict]:
        return await self._negotiation.get_watchers(listing_id)

    # === Negotiation ===

    async def respond_to_offer(
        self, listing_id: str, offer_id: str, action: str, counter_amount: float | None = None,
    ) -> dict:
        return await self._negotiation.respond_to_offer(
            listing_id, offer_id, action, counter_amount,
        )

    # === Account ===

    async def update_handling_time(self, policy_id: str, handling_days: int) -> dict:
        return await self._account.update_handling_time(policy_id, handling_days)

    # === Lifecycle ===

    async def close(self) -> None:
        """Shutdown: close HTTP client and token manager."""
        await self._http.close()
