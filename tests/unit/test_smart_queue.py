"""Tests for SmartQueue — batch release scheduling."""

from datetime import datetime

import pytz
import pytest

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, QueueStatus
from flipflow.core.models.listing import Listing
from flipflow.core.models.queue_entry import QueueEntry
from flipflow.core.services.lifecycle.smart_queue import SmartQueue
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def queue(test_config, empty_mock_ebay):
    return SmartQueue(empty_mock_ebay, test_config)


async def _create_listing(db_session, sku, title="Test Item"):
    listing = Listing(
        sku=sku, title=title, purchase_price=10, list_price=30,
        status=ListingStatus.DRAFT,
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


class TestEnqueue:
    async def test_enqueue_listing(self, queue, db_session):
        listing = await _create_listing(db_session, "Q-001")
        entry = await queue.enqueue(db_session, listing.id)
        assert entry.listing_id == listing.id
        assert entry.status == QueueStatus.PENDING
        assert entry.scheduled_window == "sunday_surge"

    async def test_enqueue_sets_listing_status(self, queue, db_session):
        listing = await _create_listing(db_session, "Q-002")
        await queue.enqueue(db_session, listing.id)
        assert listing.status == ListingStatus.QUEUED

    async def test_enqueue_with_priority(self, queue, db_session):
        listing = await _create_listing(db_session, "Q-003")
        entry = await queue.enqueue(db_session, listing.id, priority=5)
        assert entry.priority == 5

    async def test_enqueue_custom_window(self, queue, db_session):
        listing = await _create_listing(db_session, "Q-004")
        entry = await queue.enqueue(db_session, listing.id, window="immediate")
        assert entry.scheduled_window == "immediate"

    async def test_enqueue_nonexistent_raises(self, queue, db_session):
        with pytest.raises(ValueError, match="not found"):
            await queue.enqueue(db_session, 99999)


class TestReleaseBatch:
    async def test_release_publishes_to_ebay(self, queue, db_session):
        listing = await _create_listing(db_session, "R-001")
        await queue.enqueue(db_session, listing.id)
        released = await queue.release_batch(db_session)
        assert len(released) == 1
        assert released[0].status == QueueStatus.RELEASED
        assert listing.status == ListingStatus.ACTIVE
        assert listing.ebay_item_id is not None

    async def test_release_respects_batch_size(self, queue, db_session):
        for i in range(15):
            listing = await _create_listing(db_session, f"R-{i:03d}")
            await queue.enqueue(db_session, listing.id)
        released = await queue.release_batch(db_session)
        assert len(released) == 10  # Default batch size

    async def test_release_priority_ordering(self, queue, db_session):
        low = await _create_listing(db_session, "R-LOW")
        high = await _create_listing(db_session, "R-HIGH")
        await queue.enqueue(db_session, low.id, priority=1)
        await queue.enqueue(db_session, high.id, priority=10)

        released = await queue.release_batch(db_session)
        assert len(released) == 2
        # Higher priority should be first
        assert released[0].listing_id == high.id

    async def test_dry_run_no_side_effects(self, queue, db_session):
        listing = await _create_listing(db_session, "R-DRY")
        await queue.enqueue(db_session, listing.id)
        entries = await queue.release_batch(db_session, dry_run=True)
        assert len(entries) == 1
        assert entries[0].status == QueueStatus.PENDING  # Still pending
        assert listing.status == ListingStatus.QUEUED  # Still queued

    async def test_empty_queue_returns_empty(self, queue, db_session):
        released = await queue.release_batch(db_session)
        assert released == []

    async def test_release_sets_batch_id(self, queue, db_session):
        listing = await _create_listing(db_session, "R-BATCH")
        await queue.enqueue(db_session, listing.id)
        released = await queue.release_batch(db_session)
        assert released[0].batch_id is not None

    async def test_release_handles_ebay_error(self, queue, db_session, empty_mock_ebay):
        listing = await _create_listing(db_session, "R-ERR")
        await queue.enqueue(db_session, listing.id)
        empty_mock_ebay.inject_failure("create_offer", RuntimeError("eBay down"))

        released = await queue.release_batch(db_session)
        assert len(released) == 0  # Nothing successfully released

        # Check the entry was marked failed
        from sqlalchemy import select
        stmt = select(QueueEntry).where(QueueEntry.listing_id == listing.id)
        result = await db_session.execute(stmt)
        entry = result.scalar_one()
        assert entry.status == QueueStatus.FAILED
        assert "eBay down" in entry.error_message


class TestSurgeWindow:
    def test_sunday_evening_is_active(self, queue):
        # Sunday 9 PM ET
        et = pytz.timezone("America/New_York")
        dt = et.localize(datetime(2026, 2, 8, 21, 0, 0))  # Sunday
        assert queue.is_surge_window_active(dt) is True

    def test_sunday_morning_not_active(self, queue):
        et = pytz.timezone("America/New_York")
        dt = et.localize(datetime(2026, 2, 8, 10, 0, 0))  # Sunday morning
        assert queue.is_surge_window_active(dt) is False

    def test_monday_evening_not_active(self, queue):
        et = pytz.timezone("America/New_York")
        dt = et.localize(datetime(2026, 2, 9, 21, 0, 0))  # Monday
        assert queue.is_surge_window_active(dt) is False

    def test_sunday_8pm_start(self, queue):
        et = pytz.timezone("America/New_York")
        dt = et.localize(datetime(2026, 2, 8, 20, 0, 0))  # Exactly 8 PM
        assert queue.is_surge_window_active(dt) is True

    def test_sunday_10pm_end(self, queue):
        et = pytz.timezone("America/New_York")
        dt = et.localize(datetime(2026, 2, 8, 22, 0, 0))  # Exactly 10 PM (end)
        assert queue.is_surge_window_active(dt) is False

    def test_utc_conversion(self, queue):
        # Sunday 9 PM ET = Monday 2 AM UTC (during EST)
        utc_time = datetime(2026, 2, 9, 2, 0, 0, tzinfo=pytz.UTC)
        assert queue.is_surge_window_active(utc_time) is True
