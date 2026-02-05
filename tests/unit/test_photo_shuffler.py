"""Tests for Photo Shuffler — rotates main photo to improve CTR."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.lifecycle.photo_shuffler import PhotoShuffler
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def shuffler(ebay, test_config):
    return PhotoShuffler(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "PHOTO-001",
        "title": "Test Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "ebay_item_id": "EBAY-P001",
        "days_active": 20,
        "total_views": 0,
    }
    defaults.update(kwargs)
    listing = Listing(**defaults)
    return listing


class TestRotatePhotos:
    def test_swaps_first_two(self, shuffler):
        photos = ["a.jpg", "b.jpg", "c.jpg"]
        result = shuffler._rotate_photos(photos)
        assert result == ["b.jpg", "a.jpg", "c.jpg"]

    def test_two_photos(self, shuffler):
        result = shuffler._rotate_photos(["front.jpg", "back.jpg"])
        assert result == ["back.jpg", "front.jpg"]

    def test_single_photo_unchanged(self, shuffler):
        result = shuffler._rotate_photos(["only.jpg"])
        assert result == ["only.jpg"]

    def test_empty_list(self, shuffler):
        result = shuffler._rotate_photos([])
        assert result == []

    def test_does_not_mutate_original(self, shuffler):
        original = ["a.jpg", "b.jpg"]
        shuffler._rotate_photos(original)
        assert original == ["a.jpg", "b.jpg"]


class TestNeedsShuffle:
    def test_qualifies(self, shuffler):
        listing = _make_listing()
        listing.photo_urls = ["a.jpg", "b.jpg"]
        assert shuffler.needs_shuffle(listing) is True

    def test_too_few_days(self, shuffler):
        listing = _make_listing(days_active=5)
        listing.photo_urls = ["a.jpg", "b.jpg"]
        assert shuffler.needs_shuffle(listing) is False

    def test_has_views(self, shuffler):
        listing = _make_listing(total_views=5)
        listing.photo_urls = ["a.jpg", "b.jpg"]
        assert shuffler.needs_shuffle(listing) is False

    def test_single_photo(self, shuffler):
        listing = _make_listing()
        listing.photo_urls = ["only.jpg"]
        assert shuffler.needs_shuffle(listing) is False

    def test_not_active(self, shuffler):
        listing = _make_listing(status=ListingStatus.ENDED)
        listing.photo_urls = ["a.jpg", "b.jpg"]
        assert shuffler.needs_shuffle(listing) is False

    def test_no_photos(self, shuffler):
        listing = _make_listing()
        # No photos set = empty list
        assert shuffler.needs_shuffle(listing) is False


class TestScanAndShuffle:
    async def test_shuffles_qualifying_listing(self, shuffler, ebay, db_session):
        listing = _make_listing(sku="SHUF-001", days_active=20, total_views=0)
        listing.photo_urls = ["front.jpg", "back.jpg", "side.jpg"]
        db_session.add(listing)
        await db_session.flush()

        await ebay.create_inventory_item("SHUF-001", {"title": "Test"})

        result = await shuffler.scan_and_shuffle(db_session)
        assert result["candidates"] == 1
        assert result["shuffled"] == 1
        assert result["skipped"] == 0

        # Verify photos were actually rotated
        assert result["details"][0]["old_main"] == "front.jpg"
        assert result["details"][0]["new_main"] == "back.jpg"

    async def test_skips_single_photo(self, shuffler, ebay, db_session):
        listing = _make_listing(sku="SINGLE-001", days_active=20, total_views=0)
        listing.photo_urls = ["only.jpg"]
        db_session.add(listing)
        await db_session.flush()

        result = await shuffler.scan_and_shuffle(db_session)
        assert result["candidates"] == 1
        assert result["shuffled"] == 0
        assert result["skipped"] == 1
        assert "Only 1 photo" in result["skip_details"][0]["reason"]

    async def test_no_candidates(self, shuffler, db_session):
        # Listing with views > 0, shouldn't be a candidate
        listing = _make_listing(sku="VIEWED-001", total_views=50, days_active=20)
        listing.photo_urls = ["a.jpg", "b.jpg"]
        db_session.add(listing)
        await db_session.flush()

        result = await shuffler.scan_and_shuffle(db_session)
        assert result["candidates"] == 0
        assert result["shuffled"] == 0

    async def test_handles_ebay_update_error(self, shuffler, ebay, db_session):
        listing = _make_listing(sku="FAIL-001", days_active=20, total_views=0)
        listing.photo_urls = ["a.jpg", "b.jpg"]
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("update_inventory_item", RuntimeError("API error"))

        result = await shuffler.scan_and_shuffle(db_session)
        assert result["candidates"] == 1
        assert result["shuffled"] == 0
        assert result["skipped"] == 1
        assert "API error" in result["skip_details"][0]["reason"]
