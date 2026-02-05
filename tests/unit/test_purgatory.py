"""Tests for Purgatory — liquidation pricing for chronic zombies."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.growth.purgatory import Purgatory
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def purgatory(ebay, test_config):
    return Purgatory(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "PURG-001",
        "title": "Dead Weight Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "ebay_item_id": "EBAY-PG01",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestBreakEvenCalculation:
    def test_basic_break_even(self, purgatory):
        listing = _make_listing(purchase_price=20.0, shipping_cost=5.0)
        # break_even = (20 + 5 + 0.30) / (1 - 0.13 - 0.029) = 25.30 / 0.841
        result = purgatory.calculate_break_even_price(listing)
        assert abs(result - 30.08) < 0.1

    def test_zero_shipping(self, purgatory):
        listing = _make_listing(purchase_price=10.0, shipping_cost=0.0)
        # (10 + 0 + 0.30) / 0.841 = 10.30 / 0.841
        result = purgatory.calculate_break_even_price(listing)
        assert abs(result - 12.25) < 0.1

    def test_expensive_item(self, purgatory):
        listing = _make_listing(purchase_price=100.0, shipping_cost=15.0)
        result = purgatory.calculate_break_even_price(listing)
        # (100 + 15 + 0.30) / 0.841 = 115.30 / 0.841
        assert abs(result - 137.10) < 0.5


class TestMarkdownPrice:
    def test_markdown_applies_sale(self, purgatory):
        listing = _make_listing(purchase_price=20.0, shipping_cost=5.0)
        break_even = purgatory.calculate_break_even_price(listing)
        markdown = purgatory.calculate_markdown_price(listing)
        # markdown = break_even * (1 - 0.30) = break_even * 0.70
        assert abs(markdown - break_even * 0.70) < 0.01

    def test_markdown_less_than_break_even(self, purgatory):
        listing = _make_listing()
        break_even = purgatory.calculate_break_even_price(listing)
        markdown = purgatory.calculate_markdown_price(listing)
        assert markdown < break_even

    def test_sale_price_equals_break_even(self, purgatory):
        listing = _make_listing()
        sale = purgatory.calculate_sale_price(listing)
        break_even = purgatory.calculate_break_even_price(listing)
        assert abs(sale - round(break_even, 2)) < 0.01


class TestShouldSuggestDonate:
    def test_purgatory_over_7_days(self, purgatory):
        listing = _make_listing(status=ListingStatus.PURGATORY)
        assert purgatory.should_suggest_donate(listing, days_in_purgatory=7) is True

    def test_purgatory_under_7_days(self, purgatory):
        listing = _make_listing(status=ListingStatus.PURGATORY)
        assert purgatory.should_suggest_donate(listing, days_in_purgatory=5) is False

    def test_active_over_7_days(self, purgatory):
        listing = _make_listing(status=ListingStatus.ACTIVE)
        assert purgatory.should_suggest_donate(listing, days_in_purgatory=10) is False

    def test_exactly_7_days(self, purgatory):
        listing = _make_listing(status=ListingStatus.PURGATORY)
        assert purgatory.should_suggest_donate(listing, days_in_purgatory=7) is True


class TestEnterPurgatory:
    async def test_enters_purgatory(self, purgatory, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        await ebay.create_inventory_item("PURG-001", {"title": "Test"})

        result = await purgatory.enter_purgatory(db_session, listing.id)
        assert result["success"] is True
        assert result["sale_percent"] == 30.0
        assert result["markdown_price"] < result["break_even_price"]
        assert listing.status == ListingStatus.PURGATORY

    async def test_nonexistent_listing(self, purgatory, db_session):
        result = await purgatory.enter_purgatory(db_session, 9999)
        assert result["success"] is False
        assert "not found" in result["error"]

    async def test_ebay_update_failure(self, purgatory, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("bulk_update_price_quantity", RuntimeError("eBay down"))

        result = await purgatory.enter_purgatory(db_session, listing.id)
        assert result["success"] is False
        assert "eBay" in result["error"]

    async def test_price_set_to_markdown(self, purgatory, ebay, db_session):
        listing = _make_listing(purchase_price=20.0, shipping_cost=5.0)
        db_session.add(listing)
        await db_session.flush()

        await ebay.create_inventory_item("PURG-001", {"title": "Test"})

        result = await purgatory.enter_purgatory(db_session, listing.id)
        assert float(listing.current_price) == result["markdown_price"]


class TestScanForPurgatory:
    async def test_finds_stale_purgatory_listings(self, purgatory, db_session):
        listing = _make_listing(
            status=ListingStatus.PURGATORY,
            days_active=10,
        )
        listing.current_price = 15.0
        db_session.add(listing)
        await db_session.flush()

        results = await purgatory.scan_for_purgatory(db_session)
        assert len(results) == 1
        assert results[0]["suggestion"] == "DONATE_OR_TRASH"

    async def test_ignores_recent_purgatory(self, purgatory, db_session):
        listing = _make_listing(
            status=ListingStatus.PURGATORY,
            days_active=3,
        )
        listing.current_price = 15.0
        db_session.add(listing)
        await db_session.flush()

        results = await purgatory.scan_for_purgatory(db_session)
        assert len(results) == 0

    async def test_ignores_non_purgatory(self, purgatory, db_session):
        listing = _make_listing(
            status=ListingStatus.ACTIVE,
            days_active=100,
        )
        db_session.add(listing)
        await db_session.flush()

        results = await purgatory.scan_for_purgatory(db_session)
        assert len(results) == 0
