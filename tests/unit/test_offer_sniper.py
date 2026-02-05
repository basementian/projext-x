"""Tests for Offer Sniper — converts watchers into buyers."""

from datetime import datetime, timedelta, timezone

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.growth.offer_sniper import OfferSniper
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def sniper(ebay, test_config):
    return OfferSniper(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "SNIPE-001",
        "title": "Watched Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "current_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "ebay_item_id": "EBAY-S001",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestCalculateOfferPrice:
    def test_default_10_percent_off(self, sniper):
        # 10% off $50 = $45
        assert sniper.calculate_offer_price(50.0) == 45.0

    def test_rounds_to_cents(self, sniper):
        # 10% off $33.33 = $29.997 → $30.0
        result = sniper.calculate_offer_price(33.33)
        assert result == 30.0

    def test_cheap_item(self, sniper):
        # 10% off $5.99 = $5.391 → $5.39
        result = sniper.calculate_offer_price(5.99)
        assert result == 5.39

    def test_expensive_item(self, sniper):
        # 10% off $999.99 = $899.991 → $899.99
        result = sniper.calculate_offer_price(999.99)
        assert result == 899.99


class TestScanAndSnipe:
    async def test_sends_offer_to_watcher(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # Add a watcher in mock
        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1", "watchDate": "2026-01-20T10:00:00Z"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["listings_checked"] == 1
        assert result["offers_sent"] == 1
        assert result["errors"] == 0
        assert result["details"][0]["buyer_id"] == "BUYER-1"
        assert result["details"][0]["offer_price"] == 45.0

    async def test_no_watchers_no_offers(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # No watchers set on mock
        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0

    async def test_multiple_watchers_sends_one_per_cycle(self, sniper, ebay, db_session):
        """After sending to the first watcher, cooldown blocks the rest in this cycle."""
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
            {"buyerId": "BUYER-2"},
            {"buyerId": "BUYER-3"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        # Only 1 offer per listing per 24h cycle
        assert result["offers_sent"] == 1
        assert result["details"][0]["buyer_id"] == "BUYER-1"

    async def test_skips_if_offer_sent_recently(self, sniper, ebay, db_session):
        listing = _make_listing()
        listing.last_offer_sent_at = datetime.now(timezone.utc) - timedelta(hours=12)
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0

    async def test_sends_after_24h_cooldown(self, sniper, ebay, db_session):
        listing = _make_listing()
        listing.last_offer_sent_at = datetime.now(timezone.utc) - timedelta(hours=25)
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 1

    async def test_no_active_listings(self, sniper, db_session):
        result = await sniper.scan_and_snipe(db_session)
        assert result["listings_checked"] == 0
        assert result["offers_sent"] == 0

    async def test_skips_listing_without_ebay_id(self, sniper, ebay, db_session):
        listing = _make_listing(ebay_item_id=None)
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.scan_and_snipe(db_session)
        # Listing is checked but has no ebay_item_id — query still includes it
        # but get_watchers(None) returns empty
        assert result["offers_sent"] == 0

    async def test_handles_send_offer_error(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
        ]
        ebay.inject_failure("send_offer_to_buyer", RuntimeError("API error"))

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0
        assert result["errors"] == 1

    async def test_uses_current_price_over_list_price(self, sniper, ebay, db_session):
        listing = _make_listing(list_price=50.0, current_price=40.0)
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        # 10% off $40 = $36
        assert result["details"][0]["offer_price"] == 36.0
        assert result["details"][0]["original_price"] == 40.0

    async def test_skips_watcher_without_buyer_id(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"watchDate": "2026-01-20T10:00:00Z"},  # No buyerId
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0
