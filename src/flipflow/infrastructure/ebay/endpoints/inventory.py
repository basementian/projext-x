"""eBay Sell Inventory API endpoints."""

from flipflow.core.exceptions import EbayNotFoundError
from flipflow.infrastructure.ebay.http_client import EbayHttpClient


class InventoryEndpoints:
    """Maps EbayGateway inventory methods to eBay REST API calls."""

    BASE = "/sell/inventory/v1"

    def __init__(self, http: EbayHttpClient):
        self._http = http

    async def create_inventory_item(self, sku: str, item_data: dict) -> dict:
        """PUT /sell/inventory/v1/inventory_item/{sku}"""
        response = await self._http.put(
            f"{self.BASE}/inventory_item/{sku}", json=item_data,
        )
        if response.status_code == 204:
            return {"sku": sku, **item_data}
        return response.json()

    async def get_inventory_item(self, sku: str) -> dict | None:
        """GET /sell/inventory/v1/inventory_item/{sku}"""
        try:
            response = await self._http.get(f"{self.BASE}/inventory_item/{sku}")
            return response.json()
        except EbayNotFoundError:
            return None

    async def update_inventory_item(self, sku: str, item_data: dict) -> dict:
        """PUT /sell/inventory/v1/inventory_item/{sku}"""
        response = await self._http.put(
            f"{self.BASE}/inventory_item/{sku}", json=item_data,
        )
        if response.status_code == 204:
            return {"sku": sku, **item_data}
        return response.json()

    async def delete_inventory_item(self, sku: str) -> bool:
        """DELETE /sell/inventory/v1/inventory_item/{sku}"""
        try:
            await self._http.delete(f"{self.BASE}/inventory_item/{sku}")
            return True
        except EbayNotFoundError:
            return False

    async def bulk_update_price_quantity(self, updates: list[dict]) -> dict:
        """POST /sell/inventory/v1/bulk_update_price_quantity"""
        payload = {
            "requests": [
                {
                    "sku": u["sku"],
                    "shipToLocationAvailability": {
                        "quantity": u.get("quantity", 1),
                    },
                    "offers": [
                        {
                            "offerId": u.get("offerId", ""),
                            "availableQuantity": u.get("quantity", 1),
                            "price": {
                                "currency": "USD",
                                "value": str(u.get("price", "")),
                            },
                        }
                    ] if "price" in u else [],
                }
                for u in updates
            ]
        }
        response = await self._http.post(
            f"{self.BASE}/bulk_update_price_quantity", json=payload,
        )
        return response.json()
