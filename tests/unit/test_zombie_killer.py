"""Tests for Zombie Killer detection logic."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.lifecycle.zombie_killer import ZombieKiller


@pytest.fixture
def killer(test_config, empty_mock_ebay):
    return ZombieKiller(empty_mock_ebay, test_config)


async def _create_listing(
    db_session, sku, days_active, views, status="active", cycles=0, item_id=None
):
    listing = Listing(
        sku=sku,
        title=f"Test {sku}",
        purchase_price=10,
        list_price=30,
        status=status,
        days_active=days_active,
        total_views=views,
        zombie_cycle_count=cycles,
        ebay_item_id=item_id,
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


class TestZombieDetection:
    async def test_detects_old_low_view_listing(self, killer, db_session):
        await _create_listing(db_session, "Z-001", days_active=65, views=3)
        result = await killer.scan(db_session)
        assert result.zombies_found == 1
        assert result.zombies[0].sku == "Z-001"

    async def test_ignores_fresh_listing(self, killer, db_session):
        await _create_listing(db_session, "Z-002", days_active=10, views=2)
        result = await killer.scan(db_session)
        assert result.zombies_found == 0

    async def test_ignores_popular_old_listing(self, killer, db_session):
        await _create_listing(db_session, "Z-003", days_active=90, views=50)
        result = await killer.scan(db_session)
        assert result.zombies_found == 0

    async def test_boundary_exactly_at_threshold(self, killer, db_session):
        """60 days + 10 views = NOT zombie (need > and <)."""
        await _create_listing(db_session, "Z-004", days_active=60, views=10)
        result = await killer.scan(db_session)
        assert result.zombies_found == 0

    async def test_boundary_just_over(self, killer, db_session):
        """61 days + 9 views = zombie."""
        await _create_listing(db_session, "Z-005", days_active=61, views=9)
        result = await killer.scan(db_session)
        assert result.zombies_found == 1

    async def test_multiple_zombies(self, killer, db_session):
        await _create_listing(db_session, "Z-006", days_active=70, views=2)
        await _create_listing(db_session, "Z-007", days_active=100, views=0)
        await _create_listing(db_session, "Z-008", days_active=5, views=50)  # Not zombie
        result = await killer.scan(db_session)
        assert result.zombies_found == 2
        assert result.total_scanned == 3

    async def test_ignores_non_active_listings(self, killer, db_session):
        await _create_listing(db_session, "Z-009", days_active=90, views=0, status="draft")
        await _create_listing(db_session, "Z-010", days_active=90, views=0, status="ended")
        result = await killer.scan(db_session)
        assert result.zombies_found == 0
        assert result.total_scanned == 0

    async def test_empty_store(self, killer, db_session):
        result = await killer.scan(db_session)
        assert result.zombies_found == 0
        assert result.total_scanned == 0


class TestPurgatoryEscalation:
    async def test_first_cycle_not_purgatory(self, killer, db_session):
        await _create_listing(db_session, "P-001", days_active=70, views=2, cycles=0)
        result = await killer.scan(db_session)
        assert result.zombies[0].should_purgatory is False

    async def test_third_cycle_triggers_purgatory(self, killer, db_session):
        await _create_listing(db_session, "P-002", days_active=70, views=2, cycles=3)
        result = await killer.scan(db_session)
        assert result.zombies[0].should_purgatory is True
        assert result.purgatory_candidates == 1

    async def test_mixed_cycles(self, killer, db_session):
        await _create_listing(db_session, "P-003", days_active=70, views=2, cycles=1)
        await _create_listing(db_session, "P-004", days_active=80, views=1, cycles=4)
        result = await killer.scan(db_session)
        assert result.purgatory_candidates == 1


class TestFlagZombie:
    async def test_flag_sets_zombie_status(self, killer, db_session):
        listing = await _create_listing(db_session, "F-001", days_active=70, views=3)
        record = await killer.flag_zombie(db_session, listing.id)
        assert listing.status == ListingStatus.ZOMBIE
        assert record.action_taken == "flagged"
        assert record.cycle_number == 1

    async def test_flag_purgatory_if_max_cycles(self, killer, db_session):
        listing = await _create_listing(db_session, "F-002", days_active=70, views=3, cycles=3)
        record = await killer.flag_zombie(db_session, listing.id)
        assert listing.status == ListingStatus.PURGATORY
        assert record.action_taken == "purgatored"

    async def test_flag_nonexistent_listing_raises(self, killer, db_session):
        with pytest.raises(ValueError, match="not found"):
            await killer.flag_zombie(db_session, 99999)
