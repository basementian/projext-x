"""Tests for the Resurrector — kill and clone pipeline."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.lifecycle.resurrector import Resurrector


@pytest.fixture
def resurrector(test_config, empty_mock_ebay):
    return Resurrector(empty_mock_ebay, test_config)


@pytest.fixture
def mock_ebay_empty(empty_mock_ebay):
    return empty_mock_ebay


async def _create_zombie(
    db_session, sku="Z-001", offer_id="OFFER-001", item_id="ITEM-001", photos=None, cycles=0
):
    listing = Listing(
        sku=sku,
        title="Zombie Test Item",
        purchase_price=10,
        list_price=30,
        status="zombie",
        days_active=70,
        total_views=3,
        ebay_item_id=item_id,
        offer_id=offer_id,
        zombie_cycle_count=cycles,
    )
    listing.photo_urls = photos or ["https://img/1.jpg", "https://img/2.jpg", "https://img/3.jpg"]
    db_session.add(listing)
    await db_session.flush()
    return listing


class TestResurrection:
    async def test_successful_resurrection(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session)
        # Create a mock offer for withdrawal
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        result = await resurrector.resurrect(db_session, listing.id)

        assert result.success is True
        assert result.new_item_id is not None
        assert result.new_item_id != "ITEM-001"  # Different from old
        assert result.cycle_number == 1
        assert result.sku == "Z-001_R1"

    async def test_photos_rotated(self, resurrector, db_session, mock_ebay_empty):
        photos = ["https://img/a.jpg", "https://img/b.jpg", "https://img/c.jpg"]
        listing = await _create_zombie(db_session, photos=photos)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        await resurrector.resurrect(db_session, listing.id)

        # First two photos should be swapped
        assert listing.photo_urls[0] == "https://img/b.jpg"
        assert listing.photo_urls[1] == "https://img/a.jpg"
        assert listing.photo_urls[2] == "https://img/c.jpg"

    async def test_single_photo_not_rotated(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session, photos=["https://img/only.jpg"])
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        await resurrector.resurrect(db_session, listing.id)
        assert listing.photo_urls == ["https://img/only.jpg"]

    async def test_listing_resets_after_resurrection(
        self, resurrector, db_session, mock_ebay_empty
    ):
        listing = await _create_zombie(db_session)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        await resurrector.resurrect(db_session, listing.id)

        assert listing.status == ListingStatus.ACTIVE
        assert listing.days_active == 0
        assert listing.total_views == 0
        assert listing.watchers == 0
        assert listing.zombie_cycle_count == 1

    async def test_sku_generation_increments(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session, sku="NIKE-001", cycles=2)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        result = await resurrector.resurrect(db_session, listing.id)
        assert result.sku == "NIKE-001_R3"
        assert listing.zombie_cycle_count == 3

    async def test_sku_strips_old_suffix(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session, sku="NIKE-001_R1", cycles=1)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        result = await resurrector.resurrect(db_session, listing.id)
        assert result.sku == "NIKE-001_R2"

    async def test_nonexistent_listing_fails(self, resurrector, db_session):
        result = await resurrector.resurrect(db_session, 99999)
        assert result.success is False
        assert "not found" in result.error

    async def test_withdraw_failure_aborts(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session)
        mock_ebay_empty.inject_failure("withdraw_offer", RuntimeError("eBay 500"))

        result = await resurrector.resurrect(db_session, listing.id)
        assert result.success is False
        assert "withdraw" in result.error.lower()

    async def test_publish_failure_aborts(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}
        mock_ebay_empty.inject_failure("publish_offer", RuntimeError("Duplicate listing"))

        result = await resurrector.resurrect(db_session, listing.id)
        assert result.success is False
        assert "publish" in result.error.lower()

    async def test_zombie_record_created(self, resurrector, db_session, mock_ebay_empty):
        listing = await _create_zombie(db_session)
        mock_ebay_empty.offers["OFFER-001"] = {"offerId": "OFFER-001", "status": "PUBLISHED"}

        await resurrector.resurrect(db_session, listing.id)

        from sqlalchemy import select

        from flipflow.core.models.zombie_record import ZombieRecord

        stmt = select(ZombieRecord).where(ZombieRecord.listing_id == listing.id)
        result = await db_session.execute(stmt)
        records = list(result.scalars().all())
        assert len(records) == 1
        assert records[0].action_taken == "resurrected"
        assert records[0].new_item_id is not None


class TestPhotoRotation:
    def test_rotate_two_photos(self):
        r = Resurrector.__new__(Resurrector)
        result = r._rotate_photos(["a", "b"])
        assert result == ["b", "a"]

    def test_rotate_three_photos(self):
        r = Resurrector.__new__(Resurrector)
        result = r._rotate_photos(["a", "b", "c"])
        assert result == ["b", "a", "c"]

    def test_single_photo_unchanged(self):
        r = Resurrector.__new__(Resurrector)
        result = r._rotate_photos(["a"])
        assert result == ["a"]

    def test_empty_list_unchanged(self):
        r = Resurrector.__new__(Resurrector)
        result = r._rotate_photos([])
        assert result == []


class TestSKUGeneration:
    def test_first_resurrection(self):
        r = Resurrector.__new__(Resurrector)
        assert r._generate_resurrection_sku("NIKE-001", 1) == "NIKE-001_R1"

    def test_second_resurrection(self):
        r = Resurrector.__new__(Resurrector)
        assert r._generate_resurrection_sku("NIKE-001", 2) == "NIKE-001_R2"

    def test_strips_existing_suffix(self):
        r = Resurrector.__new__(Resurrector)
        assert r._generate_resurrection_sku("NIKE-001_R1", 2) == "NIKE-001_R2"

    def test_strips_deep_suffix(self):
        r = Resurrector.__new__(Resurrector)
        assert r._generate_resurrection_sku("NIKE-001_R3", 4) == "NIKE-001_R4"
