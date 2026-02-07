"""Tests for eBay Inventory endpoints."""

import httpx
import pytest

from flipflow.infrastructure.ebay.endpoints.inventory import InventoryEndpoints
from tests.unit.test_ebay_client.conftest import build_http_client


class TestCreateInventoryItem:
    async def test_creates_item_204(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "PUT"
            assert "/inventory_item/SKU-001" in str(request.url)
            return httpx.Response(204)

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        result = await ep.create_inventory_item("SKU-001", {"title": "Test"})
        assert result["sku"] == "SKU-001"
        assert result["title"] == "Test"
        await http.close()

    async def test_creates_item_200_with_body(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"sku": "SKU-002", "status": "OK"})

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        result = await ep.create_inventory_item("SKU-002", {"title": "Test"})
        assert result["sku"] == "SKU-002"
        await http.close()


class TestGetInventoryItem:
    async def test_returns_item_on_200(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "GET"
            return httpx.Response(200, json={"sku": "SKU-001", "title": "Nike"})

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        result = await ep.get_inventory_item("SKU-001")
        assert result["title"] == "Nike"
        await http.close()

    async def test_returns_none_on_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"errors": [{"message": "Not found"}]})

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        result = await ep.get_inventory_item("MISSING")
        assert result is None
        await http.close()


class TestDeleteInventoryItem:
    async def test_returns_true_on_success(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "DELETE"
            return httpx.Response(204)

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        assert await ep.delete_inventory_item("SKU-001") is True
        await http.close()

    async def test_returns_false_on_404(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, json={"errors": [{"message": "Not found"}]})

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        assert await ep.delete_inventory_item("MISSING") is False
        await http.close()


class TestBulkUpdatePriceQuantity:
    async def test_sends_bulk_payload(self):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.method == "POST"
            assert "bulk_update_price_quantity" in str(request.url)
            return httpx.Response(200, json={
                "responses": [{"sku": "SKU-001", "statusCode": 200}],
            })

        http = build_http_client(handler)
        ep = InventoryEndpoints(http)
        result = await ep.bulk_update_price_quantity([
            {"sku": "SKU-001", "price": 29.99},
        ])
        assert "responses" in result
        await http.close()
