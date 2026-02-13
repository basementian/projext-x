"""Mock eBay client — implements EbayGateway for development and testing.

Maintains stateful in-memory data so operations have observable effects.
"""

import json
import uuid
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class MockEbayClient:
    """Mock implementation of the EbayGateway protocol.

    Stores all data in-memory dicts. Fully stateful so tests can verify
    side effects (e.g. item created, offer withdrawn, photo swapped).
    """

    def __init__(self, load_fixtures: bool = True):
        self.inventory: dict[str, dict] = {}  # sku -> item_data
        self.offers: dict[str, dict] = {}  # offer_id -> offer_data
        self.campaigns: dict[str, dict] = {}  # campaign_id -> campaign_data
        self.watchers: dict[str, list[dict]] = {}  # listing_id -> [watcher_data]
        self.traffic: dict[str, dict] = {}  # listing_id -> traffic_data
        self._next_listing_id = 200000
        self._failure_injection: dict[str, Exception] = {}

        if load_fixtures:
            self._load_fixtures()

    def _load_fixtures(self):
        """Load fixture data from JSON files."""
        items_file = FIXTURES_DIR / "inventory_items.json"
        if items_file.exists():
            items = json.loads(items_file.read_text())
            for item in items:
                sku = item["sku"]
                listing_id = item.get("listing_id", f"MOCK-{self._next_listing_id}")
                self.inventory[sku] = item

                # Create corresponding offer
                offer_id = f"OFFER-{listing_id}"
                self.offers[offer_id] = {
                    "offerId": offer_id,
                    "sku": sku,
                    "listingId": listing_id,
                    "status": "PUBLISHED",
                    "pricingSummary": {"price": {"value": str(item["price"]), "currency": "USD"}},
                }

                # Create traffic data
                self.traffic[listing_id] = {
                    "listingId": listing_id,
                    "views": item.get("views", 0),
                    "impressions": item.get("views", 0) * 10,
                    "clicks": item.get("views", 0) // 3,
                }

                # Some items get watchers
                if item.get("watchers", 0) > 0:
                    self.watchers[listing_id] = [
                        {"buyerId": f"BUYER-{i}", "watchDate": "2026-01-15T10:00:00Z"}
                        for i in range(item["watchers"])
                    ]

    def inject_failure(self, method_name: str, error: Exception):
        """Configure a method to raise an error on next call (for testing error paths)."""
        self._failure_injection[method_name] = error

    def _check_failure(self, method_name: str):
        if method_name in self._failure_injection:
            error = self._failure_injection.pop(method_name)
            raise error

    # === Inventory Management ===

    async def create_inventory_item(self, sku: str, item_data: dict) -> dict:
        self._check_failure("create_inventory_item")
        self.inventory[sku] = {**item_data, "sku": sku}
        return self.inventory[sku]

    async def get_inventory_item(self, sku: str) -> dict | None:
        self._check_failure("get_inventory_item")
        return self.inventory.get(sku)

    async def update_inventory_item(self, sku: str, item_data: dict) -> dict:
        self._check_failure("update_inventory_item")
        if sku not in self.inventory:
            raise KeyError(f"SKU {sku} not found")
        self.inventory[sku].update(item_data)
        return self.inventory[sku]

    async def delete_inventory_item(self, sku: str) -> bool:
        self._check_failure("delete_inventory_item")
        if sku in self.inventory:
            del self.inventory[sku]
            return True
        return False

    async def bulk_update_price_quantity(self, updates: list[dict]) -> dict:
        self._check_failure("bulk_update_price_quantity")
        results = []
        for update in updates:
            sku = update.get("sku")
            if sku in self.inventory:
                if "price" in update:
                    self.inventory[sku]["price"] = update["price"]
                results.append({"sku": sku, "status": "SUCCESS"})
            else:
                results.append({"sku": sku, "status": "NOT_FOUND"})
        return {"responses": results}

    # === Offer Management ===

    async def create_offer(self, offer_data: dict) -> dict:
        self._check_failure("create_offer")
        offer_id = f"OFFER-{uuid.uuid4().hex[:8]}"
        offer = {**offer_data, "offerId": offer_id, "status": "CREATED"}
        self.offers[offer_id] = offer
        return offer

    async def publish_offer(self, offer_id: str) -> dict:
        self._check_failure("publish_offer")
        if offer_id not in self.offers:
            raise KeyError(f"Offer {offer_id} not found")
        self.offers[offer_id]["status"] = "PUBLISHED"
        listing_id = f"MOCK-{self._next_listing_id}"
        self._next_listing_id += 1
        self.offers[offer_id]["listingId"] = listing_id
        return {"listingId": listing_id, "offerId": offer_id}

    async def withdraw_offer(self, offer_id: str) -> dict:
        self._check_failure("withdraw_offer")
        if offer_id not in self.offers:
            raise KeyError(f"Offer {offer_id} not found")
        self.offers[offer_id]["status"] = "WITHDRAWN"
        return {"offerId": offer_id, "status": "WITHDRAWN"}

    async def get_offer(self, offer_id: str) -> dict | None:
        self._check_failure("get_offer")
        return self.offers.get(offer_id)

    async def get_offers_by_sku(self, sku: str) -> list[dict]:
        self._check_failure("get_offers_by_sku")
        return [o for o in self.offers.values() if o.get("sku") == sku]

    # === Analytics ===

    async def get_traffic_report(
        self, listing_ids: list[str], date_range: str, metrics: list[str],
    ) -> dict:
        self._check_failure("get_traffic_report")
        records = []
        for lid in listing_ids:
            data = self.traffic.get(lid, {"listingId": lid, "views": 0, "impressions": 0, "clicks": 0})
            records.append(data)
        return {"records": records}

    # === Marketing ===

    async def create_campaign(self, campaign_data: dict) -> dict:
        self._check_failure("create_campaign")
        campaign_id = f"CAMP-{uuid.uuid4().hex[:8]}"
        campaign = {**campaign_data, "campaignId": campaign_id, "status": "RUNNING"}
        self.campaigns[campaign_id] = campaign
        return campaign

    async def end_campaign(self, campaign_id: str) -> bool:
        self._check_failure("end_campaign")
        if campaign_id in self.campaigns:
            self.campaigns[campaign_id]["status"] = "ENDED"
            return True
        return False

    async def get_campaign(self, campaign_id: str) -> dict | None:
        self._check_failure("get_campaign")
        return self.campaigns.get(campaign_id)

    # === Browse ===

    async def search_items(self, query: str, filters: dict | None = None) -> dict:
        self._check_failure("search_items")
        results = []
        query_lower = query.lower()
        for item in self.inventory.values():
            if query_lower in item.get("title", "").lower():
                results.append(item)
        return {"itemSummaries": results, "total": len(results)}

    # === Buyer Engagement ===

    async def send_offer_to_buyer(
        self, listing_id: str, buyer_id: str, offer_data: dict,
    ) -> dict:
        self._check_failure("send_offer_to_buyer")
        return {
            "listingId": listing_id,
            "buyerId": buyer_id,
            "status": "SENT",
            **offer_data,
        }

    async def get_watchers(self, listing_id: str) -> list[dict]:
        self._check_failure("get_watchers")
        return self.watchers.get(listing_id, [])

    # === Negotiation ===

    async def respond_to_offer(
        self, listing_id: str, offer_id: str, action: str, counter_amount: float | None = None,
    ) -> dict:
        self._check_failure("respond_to_offer")
        return {
            "listingId": listing_id,
            "offerId": offer_id,
            "action": action,
            "counterAmount": counter_amount,
            "status": "SUCCESS",
        }

    # === Account ===

    async def update_handling_time(self, policy_id: str, handling_days: int) -> dict:
        self._check_failure("update_handling_time")
        return {"policyId": policy_id, "handlingDays": handling_days, "status": "UPDATED"}
