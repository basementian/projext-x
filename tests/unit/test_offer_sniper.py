"""Tests for Offer Sniper V2 — tiered offers, per-watcher cooldown, inbound handling."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from flipflow.core.constants import ListingStatus, OfferAction, OfferStatus
from flipflow.core.models.listing import Listing
from flipflow.core.models.offer_record import OfferRecord
from flipflow.core.services.growth.offer_sniper import OfferSniper, _parse_tiers
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
        "days_active": 0,
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestParseTiers:
    def test_default_tiers(self):
        tiers = _parse_tiers("0:5,14:10,30:15,45:20")
        assert tiers == [(0, 5.0), (14, 10.0), (30, 15.0), (45, 20.0)]

    def test_sorts_by_days(self):
        tiers = _parse_tiers("30:15,0:5,14:10")
        assert tiers == [(0, 5.0), (14, 10.0), (30, 15.0)]

    def test_empty_string(self):
        assert _parse_tiers("") == []


class TestGetDiscountPercent:
    def test_new_listing_gets_5_percent(self, sniper):
        assert sniper.get_discount_percent(0) == 5.0

    def test_7_days_still_5_percent(self, sniper):
        assert sniper.get_discount_percent(7) == 5.0

    def test_14_days_gets_10_percent(self, sniper):
        assert sniper.get_discount_percent(14) == 10.0

    def test_30_days_gets_15_percent(self, sniper):
        assert sniper.get_discount_percent(30) == 15.0

    def test_45_days_gets_20_percent(self, sniper):
        assert sniper.get_discount_percent(45) == 20.0

    def test_between_tiers(self, sniper):
        # 20 days → still tier 2 (14 days)
        assert sniper.get_discount_percent(20) == 10.0


class TestCalculateOfferPrice:
    def test_new_listing_5_percent_off(self, sniper):
        # 5% off $50 = $47.50
        assert sniper.calculate_offer_price(50.0, days_active=0) == 47.5

    def test_14_day_listing_10_percent_off(self, sniper):
        # 10% off $50 = $45
        assert sniper.calculate_offer_price(50.0, days_active=14) == 45.0

    def test_30_day_listing_15_percent_off(self, sniper):
        # 15% off $50 = $42.50
        assert sniper.calculate_offer_price(50.0, days_active=30) == 42.5

    def test_45_day_listing_20_percent_off(self, sniper):
        # 20% off $50 = $40
        assert sniper.calculate_offer_price(50.0, days_active=45) == 40.0

    def test_rounds_to_cents(self, sniper):
        # 5% off $33.33 = $31.6635 → $31.66
        result = sniper.calculate_offer_price(33.33, days_active=0)
        assert result == 31.66

    def test_backwards_compatible_default(self, sniper):
        # days_active defaults to 0
        assert sniper.calculate_offer_price(50.0) == 47.5


class TestScanAndSnipe:
    async def test_sends_tiered_offer_to_watcher(self, sniper, ebay, db_session):
        listing = _make_listing(days_active=14)
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1", "watchDate": "2026-01-20T10:00:00Z"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["listings_checked"] == 1
        assert result["offers_sent"] == 1
        assert result["details"][0]["buyer_id"] == "BUYER-1"
        assert result["details"][0]["offer_price"] == 45.0  # 10% off at 14 days
        assert result["details"][0]["discount_percent"] == 10.0

    async def test_no_watchers_no_offers(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0

    async def test_multiple_watchers_all_get_offers(self, sniper, ebay, db_session):
        """Per-watcher cooldown: all watchers get offers in the same cycle."""
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},
            {"buyerId": "BUYER-2"},
            {"buyerId": "BUYER-3"},
        ]

        result = await sniper.scan_and_snipe(db_session)
        # Now all 3 watchers get offers (per-watcher cooldown, not per-listing)
        assert result["offers_sent"] == 3

    async def test_per_watcher_cooldown(self, sniper, ebay, db_session):
        """A watcher who already got an offer in the last 24h is skipped."""
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # Pre-existing offer record for BUYER-1 (sent 12 hours ago)
        record = OfferRecord(
            listing_id=listing.id,
            buyer_id="BUYER-1",
            offer_price=47.5,
            discount_percent=5.0,
            sent_at=datetime.now(UTC) - timedelta(hours=12),
            status=OfferStatus.SENT,
        )
        db_session.add(record)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"buyerId": "BUYER-1"},  # Should be skipped (recent offer)
            {"buyerId": "BUYER-2"},  # Should get offer
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 1
        assert result["details"][0]["buyer_id"] == "BUYER-2"

    async def test_cooldown_expires_after_24h(self, sniper, ebay, db_session):
        """After 24h, a watcher can get a new offer."""
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # Offer sent 25 hours ago — expired
        record = OfferRecord(
            listing_id=listing.id,
            buyer_id="BUYER-1",
            offer_price=47.5,
            discount_percent=5.0,
            sent_at=datetime.now(UTC) - timedelta(hours=25),
            status=OfferStatus.SENT,
        )
        db_session.add(record)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [{"buyerId": "BUYER-1"}]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 1

    async def test_creates_offer_records(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [{"buyerId": "BUYER-1"}]

        await sniper.scan_and_snipe(db_session)

        stmt = select(OfferRecord).where(OfferRecord.listing_id == listing.id)
        result = await db_session.execute(stmt)
        records = list(result.scalars().all())
        assert len(records) == 1
        assert records[0].buyer_id == "BUYER-1"
        assert records[0].status == OfferStatus.SENT

    async def test_no_active_listings(self, sniper, db_session):
        result = await sniper.scan_and_snipe(db_session)
        assert result["listings_checked"] == 0
        assert result["offers_sent"] == 0

    async def test_skips_watcher_without_buyer_id(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [
            {"watchDate": "2026-01-20T10:00:00Z"},  # No buyerId
        ]

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0

    async def test_handles_send_offer_error(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [{"buyerId": "BUYER-1"}]
        ebay.inject_failure("send_offer_to_buyer", RuntimeError("API error"))

        result = await sniper.scan_and_snipe(db_session)
        assert result["offers_sent"] == 0
        assert result["errors"] == 1

    async def test_uses_current_price_over_list_price(self, sniper, ebay, db_session):
        listing = _make_listing(list_price=50.0, current_price=40.0, days_active=0)
        db_session.add(listing)
        await db_session.flush()

        ebay.watchers["EBAY-S001"] = [{"buyerId": "BUYER-1"}]

        result = await sniper.scan_and_snipe(db_session)
        # 5% off $40 = $38
        assert result["details"][0]["offer_price"] == 38.0
        assert result["details"][0]["original_price"] == 40.0


class TestHandleIncomingOffer:
    async def test_auto_accept_above_90_percent(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 46.0,
        )
        assert result["success"] is True
        assert result["action"] == OfferAction.ACCEPT
        assert result["ratio"] == 0.92
        assert result["counter_amount"] is None

    async def test_counter_between_75_and_90_percent(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 40.0,
        )
        assert result["success"] is True
        assert result["action"] == OfferAction.COUNTER
        assert result["ratio"] == 0.8
        assert result["counter_amount"] == 47.5  # 95% of $50

    async def test_reject_below_75_percent(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 30.0,
        )
        assert result["success"] is True
        assert result["action"] == OfferAction.REJECT
        assert result["ratio"] == 0.6
        assert result["counter_amount"] is None

    async def test_exact_90_percent_is_accepted(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 45.0,
        )
        assert result["action"] == OfferAction.ACCEPT

    async def test_exact_75_percent_is_countered(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 37.5,
        )
        assert result["action"] == OfferAction.COUNTER

    async def test_creates_offer_record(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 46.0,
        )

        stmt = select(OfferRecord).where(OfferRecord.listing_id == listing.id)
        result = await db_session.execute(stmt)
        records = list(result.scalars().all())
        assert len(records) == 1
        assert records[0].buyer_id == "BUYER-1"
        assert float(records[0].offer_price) == 46.0
        assert records[0].status == OfferStatus.ACCEPTED

    async def test_listing_not_found(self, sniper, db_session):
        result = await sniper.handle_incoming_offer(
            db_session, 999, "BUYER-1", "OFFER-123", 40.0,
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    async def test_handles_ebay_error(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("respond_to_offer", RuntimeError("API down"))

        result = await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 46.0,
        )
        assert result["success"] is False
        assert "API" in result["error"]

    async def test_counter_record_has_sent_status(self, sniper, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        await sniper.handle_incoming_offer(
            db_session, listing.id, "BUYER-1", "OFFER-123", 40.0,
        )

        stmt = select(OfferRecord).where(OfferRecord.listing_id == listing.id)
        result = await db_session.execute(stmt)
        record = result.scalars().first()
        # Counter offers are recorded as SENT (pending buyer response)
        assert record.status == OfferStatus.SENT
