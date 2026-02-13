"""EbayGateway protocol — the central abstraction for all eBay API interactions.

Every service depends on this protocol, never on a concrete eBay client.
Implementations: MockEbayClient (dev/test), RealEbayClient (production).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EbayGateway(Protocol):

    # === Inventory Management ===

    async def create_inventory_item(self, sku: str, item_data: dict) -> dict:
        """Create or replace an inventory item."""
        ...

    async def get_inventory_item(self, sku: str) -> dict | None:
        """Get an inventory item by SKU. Returns None if not found."""
        ...

    async def update_inventory_item(self, sku: str, item_data: dict) -> dict:
        """Update an existing inventory item."""
        ...

    async def delete_inventory_item(self, sku: str) -> bool:
        """Delete an inventory item. Returns True if successful."""
        ...

    async def bulk_update_price_quantity(self, updates: list[dict]) -> dict:
        """Bulk update prices and quantities for multiple items."""
        ...

    # === Offer Management ===

    async def create_offer(self, offer_data: dict) -> dict:
        """Create an offer for an inventory item."""
        ...

    async def publish_offer(self, offer_id: str) -> dict:
        """Publish an offer to make it live. Returns dict with listingId."""
        ...

    async def withdraw_offer(self, offer_id: str) -> dict:
        """Withdraw (end) a published offer."""
        ...

    async def get_offer(self, offer_id: str) -> dict | None:
        """Get offer details by offer ID."""
        ...

    async def get_offers_by_sku(self, sku: str) -> list[dict]:
        """Get all offers for a given SKU."""
        ...

    # === Analytics ===

    async def get_traffic_report(
        self, listing_ids: list[str], date_range: str, metrics: list[str],
    ) -> dict:
        """Get traffic report (views, impressions, clicks) for listings."""
        ...

    # === Marketing (Promoted Listings) ===

    async def create_campaign(self, campaign_data: dict) -> dict:
        """Create a Promoted Listings campaign."""
        ...

    async def end_campaign(self, campaign_id: str) -> bool:
        """End a running campaign. Returns True if successful."""
        ...

    async def get_campaign(self, campaign_id: str) -> dict | None:
        """Get campaign details."""
        ...

    # === Browse (Search) ===

    async def search_items(self, query: str, filters: dict | None = None) -> dict:
        """Search for items on eBay marketplace."""
        ...

    # === Buyer Engagement ===

    async def send_offer_to_buyer(
        self, listing_id: str, buyer_id: str, offer_data: dict,
    ) -> dict:
        """Send a private offer to a specific buyer."""
        ...

    async def get_watchers(self, listing_id: str) -> list[dict]:
        """Get list of watchers for a listing."""
        ...

    # === Negotiation ===

    async def respond_to_offer(
        self, listing_id: str, offer_id: str, action: str, counter_amount: float | None = None,
    ) -> dict:
        """Respond to an incoming buyer offer (accept, counter, or reject)."""
        ...

    # === Account ===

    async def update_handling_time(self, policy_id: str, handling_days: int) -> dict:
        """Update handling time on a business policy."""
        ...
