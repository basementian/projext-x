"""Integration tests for RealEbayClient — protocol compliance and wiring."""

import pytest

from flipflow.core.config import FlipFlowConfig
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.infrastructure.ebay.client import RealEbayClient


@pytest.fixture
def sandbox_config():
    return FlipFlowConfig(
        database_url="sqlite+aiosqlite:///:memory:",
        ebay_mode="sandbox",
        ebay_client_id="test-id",
        ebay_client_secret="test-secret",
        ebay_refresh_token="test-refresh",
    )


class TestProtocolCompliance:
    def test_satisfies_ebay_gateway_protocol(self, sandbox_config):
        client = RealEbayClient(sandbox_config)
        assert isinstance(client, EbayGateway)

    def test_has_all_18_protocol_methods(self, sandbox_config):
        client = RealEbayClient(sandbox_config)
        expected_methods = [
            # Inventory (5)
            "create_inventory_item",
            "get_inventory_item",
            "update_inventory_item",
            "delete_inventory_item",
            "bulk_update_price_quantity",
            # Offers (5)
            "create_offer",
            "publish_offer",
            "withdraw_offer",
            "get_offer",
            "get_offers_by_sku",
            # Analytics (1)
            "get_traffic_report",
            # Marketing (3)
            "create_campaign",
            "end_campaign",
            "get_campaign",
            # Browse (1)
            "search_items",
            # Buyer Engagement (2)
            "send_offer_to_buyer",
            "get_watchers",
            # Negotiation (1)
            "respond_to_offer",
            # Account (1)
            "update_handling_time",
        ]
        for method in expected_methods:
            assert hasattr(client, method), f"Missing method: {method}"
            assert callable(getattr(client, method))


class TestConstruction:
    def test_creates_with_empty_credentials(self):
        """Client can be constructed without valid credentials (lazy token fetch)."""
        config = FlipFlowConfig(
            database_url="sqlite+aiosqlite:///:memory:",
            ebay_mode="sandbox",
            ebay_client_id="",
            ebay_client_secret="",
            ebay_refresh_token="",
        )
        client = RealEbayClient(config)
        assert client is not None

    def test_sandbox_mode_uses_sandbox_url(self, sandbox_config):
        client = RealEbayClient(sandbox_config)
        assert "sandbox" in client._token_manager._base_url

    def test_production_mode_uses_production_url(self):
        config = FlipFlowConfig(
            database_url="sqlite+aiosqlite:///:memory:",
            ebay_mode="production",
            ebay_client_id="prod-id",
            ebay_client_secret="prod-secret",
            ebay_refresh_token="prod-refresh",
        )
        client = RealEbayClient(config)
        assert "sandbox" not in client._token_manager._base_url
        assert "api.ebay.com" in client._token_manager._base_url


class TestClose:
    async def test_close_cascades(self, sandbox_config):
        client = RealEbayClient(sandbox_config)
        await client.close()
        # Token manager's HTTP client should be None after close
        assert client._token_manager._http is None
