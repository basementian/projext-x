"""Tests for Store Pulse — handling time toggle for store re-indexing."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.lifecycle.store_pulse import StorePulse
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def pulse(ebay, test_config):
    return StorePulse(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "TEST-001",
        "title": "Test Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "ebay_item_id": "EBAY-12345",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestToggleHandlingTime:
    async def test_toggles_active_listings(self, pulse, ebay, db_session):
        listing = _make_listing(sku="PULSE-001")
        db_session.add(listing)
        await db_session.flush()

        # Register SKU in mock eBay so bulk update finds it
        await ebay.create_inventory_item("PULSE-001", {"title": "Test"})

        result = await pulse.toggle_handling_time(db_session, target_days=2)
        assert result["updated"] == 1
        assert result["errors"] == 0
        assert result["target_handling_days"] == 2

    async def test_no_active_listings(self, pulse, db_session):
        result = await pulse.toggle_handling_time(db_session)
        assert result["updated"] == 0
        assert result["message"] == "No active listings"

    async def test_skips_listings_without_ebay_id(self, pulse, db_session):
        listing = _make_listing(sku="NO-EBAY", ebay_item_id=None)
        db_session.add(listing)
        await db_session.flush()

        result = await pulse.toggle_handling_time(db_session)
        assert result["updated"] == 0
        assert result["message"] == "No listings with eBay IDs"

    async def test_multiple_listings(self, pulse, ebay, db_session):
        for i in range(3):
            listing = _make_listing(
                sku=f"MULTI-{i}",
                ebay_item_id=f"EBAY-{i}",
            )
            db_session.add(listing)
            await ebay.create_inventory_item(f"MULTI-{i}", {"title": f"Item {i}"})
        await db_session.flush()

        result = await pulse.toggle_handling_time(db_session, target_days=2)
        assert result["updated"] == 3
        assert result["total_active"] == 3

    async def test_ignores_non_active_listings(self, pulse, ebay, db_session):
        active = _make_listing(sku="ACTIVE-1", ebay_item_id="E-1")
        sold = _make_listing(sku="SOLD-1", ebay_item_id="E-2", status=ListingStatus.SOLD)
        db_session.add_all([active, sold])
        await db_session.flush()

        await ebay.create_inventory_item("ACTIVE-1", {"title": "Active"})
        await ebay.create_inventory_item("SOLD-1", {"title": "Sold"})

        result = await pulse.toggle_handling_time(db_session, target_days=2)
        assert result["updated"] == 1
        assert result["total_active"] == 1

    async def test_handles_ebay_error(self, pulse, ebay, db_session):
        listing = _make_listing(sku="ERR-1")
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("bulk_update_price_quantity", RuntimeError("API down"))

        result = await pulse.toggle_handling_time(db_session, target_days=2)
        assert result["errors"] > 0
        assert "error_message" in result


class TestRevertHandlingTime:
    async def test_reverts_to_one_day(self, pulse, ebay, db_session):
        listing = _make_listing(sku="REVERT-1")
        db_session.add(listing)
        await db_session.flush()

        await ebay.create_inventory_item("REVERT-1", {"title": "Test"})

        result = await pulse.revert_handling_time(db_session)
        assert result["target_handling_days"] == 1
        assert result["updated"] == 1
