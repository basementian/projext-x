"""Integration tests for database models."""

from datetime import datetime, timezone

import pytest

from flipflow.core.models import (
    Listing,
    ListingSnapshot,
    QueueEntry,
    ZombieRecord,
    Campaign,
    ProfitRecord,
    JobLog,
)
from flipflow.infrastructure.database.repository import Repository


@pytest.fixture
def repo(db_session):
    return Repository(db_session)


class TestListingModel:
    async def test_create_listing(self, db_session, repo):
        listing = Listing(
            sku="TEST-001",
            title="Nike Air Max 90",
            purchase_price=25.00,
            list_price=50.00,
        )
        created = await repo.create(listing)
        assert created.id is not None
        assert created.sku == "TEST-001"
        assert created.status == "draft"

    async def test_listing_defaults(self, db_session, repo):
        listing = Listing(
            sku="TEST-002",
            title="Test Item",
            purchase_price=10,
            list_price=30,
        )
        await repo.create(listing)
        assert listing.days_active == 0
        assert listing.total_views == 0
        assert listing.watchers == 0
        assert listing.zombie_cycle_count == 0
        assert listing.main_photo_index == 0

    async def test_photo_urls_property(self, db_session, repo):
        listing = Listing(
            sku="TEST-003",
            title="Photo Test",
            purchase_price=10,
            list_price=30,
        )
        listing.photo_urls = ["https://example.com/1.jpg", "https://example.com/2.jpg"]
        await repo.create(listing)

        fetched = await repo.get(Listing, listing.id)
        assert fetched.photo_urls == ["https://example.com/1.jpg", "https://example.com/2.jpg"]

    async def test_update_listing(self, db_session, repo):
        listing = Listing(
            sku="TEST-004",
            title="Update Test",
            purchase_price=10,
            list_price=30,
        )
        await repo.create(listing)
        await repo.update(listing, status="active", total_views=5)
        assert listing.status == "active"
        assert listing.total_views == 5


class TestRelationships:
    async def test_listing_snapshot_relationship(self, db_session, repo):
        listing = Listing(
            sku="REL-001",
            title="Snapshot Test",
            purchase_price=10,
            list_price=30,
        )
        await repo.create(listing)

        from datetime import date
        snapshot = ListingSnapshot(
            listing_id=listing.id,
            snapshot_date=date.today(),
            views=15,
            impressions=100,
            watchers=3,
            price_at_snapshot=30.00,
            status_at_snapshot="active",
        )
        await repo.create(snapshot)
        assert snapshot.listing_id == listing.id

    async def test_zombie_record_relationship(self, db_session, repo):
        listing = Listing(
            sku="REL-002",
            title="Zombie Test",
            purchase_price=10,
            list_price=30,
        )
        await repo.create(listing)

        record = ZombieRecord(
            listing_id=listing.id,
            detected_at=datetime.now(timezone.utc),
            days_active_at_detection=65,
            views_at_detection=3,
            action_taken="flagged",
            cycle_number=1,
        )
        await repo.create(record)
        assert record.listing_id == listing.id

    async def test_queue_entry_relationship(self, db_session, repo):
        listing = Listing(
            sku="REL-003",
            title="Queue Test",
            purchase_price=10,
            list_price=30,
        )
        await repo.create(listing)

        entry = QueueEntry(
            listing_id=listing.id,
            priority=5,
            scheduled_window="sunday_surge",
        )
        await repo.create(entry)
        assert entry.status == "pending"


class TestQueryFilters:
    async def test_filter_by_status(self, db_session, repo):
        for i, status in enumerate(["draft", "active", "active", "zombie"]):
            listing = Listing(
                sku=f"FILTER-{i:03d}",
                title=f"Filter Test {i}",
                purchase_price=10,
                list_price=30,
                status=status,
            )
            await repo.create(listing)

        active = await repo.get_all(Listing, status="active")
        assert len(active) == 2

        zombies = await repo.get_all(Listing, status="zombie")
        assert len(zombies) == 1


class TestJobLog:
    async def test_create_job_log(self, db_session, repo):
        log = JobLog(
            job_name="zombie_scan",
            job_type="zombie_scan",
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        await repo.create(log)
        assert log.id is not None
        assert log.items_processed == 0
