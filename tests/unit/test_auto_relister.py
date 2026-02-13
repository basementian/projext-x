"""Tests for Auto Relister — proactive scheduled relisting."""

import pytest
from sqlalchemy import select

from flipflow.core.constants import ListingStatus, RelistAction
from flipflow.core.models.listing import Listing
from flipflow.core.models.zombie_record import ZombieRecord
from flipflow.core.services.lifecycle.auto_relister import AutoRelister
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def relister(ebay, test_config):
    return AutoRelister(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "RELIST-001",
        "title": "Relist Test Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "current_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "days_active": 35,
        "total_views": 5,
        "watchers": 0,
        "ebay_item_id": "EBAY-RL001",
        "offer_id": "OFFER-RL001",
        "zombie_cycle_count": 0,
        "photo_urls_json": '["photo1.jpg", "photo2.jpg"]',
        "condition_id": "3000",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


async def _setup_ebay(ebay, sku="RELIST-001", offer_id="OFFER-RL001"):
    """Create inventory item and offer in mock eBay."""
    await ebay.create_inventory_item(sku, {"title": "Test", "price": 50.0})
    ebay.offers[offer_id] = {
        "offerId": offer_id,
        "sku": sku,
        "status": "PUBLISHED",
    }


class TestIsDueForRelist:
    def test_eligible_listing(self, relister):
        listing = _make_listing(days_active=35, total_views=5)
        assert relister._is_due_for_relist(listing) is True

    def test_too_young(self, relister):
        listing = _make_listing(days_active=20)
        assert relister._is_due_for_relist(listing) is False

    def test_too_many_views(self, relister):
        listing = _make_listing(days_active=35, total_views=100)
        assert relister._is_due_for_relist(listing) is False

    def test_exactly_at_cadence(self, relister):
        listing = _make_listing(days_active=30, total_views=5)
        assert relister._is_due_for_relist(listing) is True

    def test_exactly_at_views_threshold(self, relister):
        # views == threshold → NOT eligible (must be strictly less)
        listing = _make_listing(days_active=35, total_views=50)
        assert relister._is_due_for_relist(listing) is False

    def test_non_active_status(self, relister):
        listing = _make_listing(status=ListingStatus.ZOMBIE)
        assert relister._is_due_for_relist(listing) is False

    def test_no_offer_id(self, relister):
        listing = _make_listing(offer_id=None)
        assert relister._is_due_for_relist(listing) is False


class TestScanForRelists:
    async def test_finds_candidates(self, relister, db_session):
        listing = _make_listing(days_active=35, total_views=5)
        db_session.add(listing)
        await db_session.flush()

        candidates = await relister.scan_for_relists(db_session)
        assert len(candidates) == 1
        assert candidates[0]["sku"] == "RELIST-001"
        assert candidates[0]["days_active"] == 35

    async def test_excludes_high_traffic(self, relister, db_session):
        listing = _make_listing(total_views=100)
        db_session.add(listing)
        await db_session.flush()

        candidates = await relister.scan_for_relists(db_session)
        assert len(candidates) == 0

    async def test_empty_store(self, relister, db_session):
        candidates = await relister.scan_for_relists(db_session)
        assert len(candidates) == 0


class TestAutoRelist:
    async def test_relists_eligible_listing(self, relister, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()
        await _setup_ebay(ebay)

        result = await relister.auto_relist(db_session)
        assert result["relisted"] == 1
        assert result["errors"] == 0
        assert result["details"][0]["old_item_id"] == "EBAY-RL001"
        assert result["details"][0]["new_item_id"] is not None

    async def test_preserves_zombie_cycle_count(self, relister, ebay, db_session):
        listing = _make_listing(zombie_cycle_count=2)
        db_session.add(listing)
        await db_session.flush()
        await _setup_ebay(ebay)

        await relister.auto_relist(db_session)
        # zombie_cycle_count should be restored — preventive relist is NOT a zombie cycle
        assert listing.zombie_cycle_count == 2

    async def test_creates_preventive_relist_record(self, relister, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()
        await _setup_ebay(ebay)

        await relister.auto_relist(db_session)

        # Should have 2 zombie records: one from resurrector (RESURRECTED) and one from us (PREVENTIVE_RELIST)
        stmt = select(ZombieRecord).where(
            ZombieRecord.listing_id == listing.id,
            ZombieRecord.action_taken == RelistAction.PREVENTIVE_RELIST,
        )
        result = await db_session.execute(stmt)
        records = list(result.scalars().all())
        assert len(records) == 1
        assert records[0].old_item_id == "EBAY-RL001"

    async def test_skips_young_listings(self, relister, db_session):
        listing = _make_listing(days_active=10)
        db_session.add(listing)
        await db_session.flush()

        result = await relister.auto_relist(db_session)
        assert result["relisted"] == 0
        assert result["skipped"] == 1

    async def test_skips_high_traffic(self, relister, db_session):
        listing = _make_listing(total_views=100)
        db_session.add(listing)
        await db_session.flush()

        result = await relister.auto_relist(db_session)
        assert result["relisted"] == 0
        assert result["skipped"] == 1

    async def test_handles_resurrect_failure(self, relister, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()
        # Don't set up eBay — offer_id won't exist in mock, withdraw will fail
        ebay.inject_failure("withdraw_offer", RuntimeError("Not found"))

        result = await relister.auto_relist(db_session)
        assert result["relisted"] == 0
        assert result["errors"] == 1

    async def test_resets_days_and_views(self, relister, ebay, db_session):
        listing = _make_listing(days_active=40, total_views=8)
        db_session.add(listing)
        await db_session.flush()
        await _setup_ebay(ebay)

        await relister.auto_relist(db_session)
        assert listing.days_active == 0
        assert listing.total_views == 0
        assert listing.status == ListingStatus.ACTIVE

    async def test_gets_new_item_id(self, relister, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()
        await _setup_ebay(ebay)

        old_id = listing.ebay_item_id
        await relister.auto_relist(db_session)
        assert listing.ebay_item_id != old_id
        assert listing.ebay_item_id is not None

    async def test_no_active_listings(self, relister, db_session):
        result = await relister.auto_relist(db_session)
        assert result["total_scanned"] == 0
        assert result["relisted"] == 0
