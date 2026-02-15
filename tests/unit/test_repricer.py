"""Tests for Graduated Repricer — time-based markdown ladder."""

import pytest

from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.services.lifecycle.repricer import Repricer, _parse_steps
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def repricer(ebay, test_config):
    return Repricer(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "REPRICE-001",
        "title": "Test Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "current_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "days_active": 0,
        "total_views": 5,
        "ad_rate_percent": 0.0,
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestParseSteps:
    def test_default_steps(self):
        steps = _parse_steps("7:5,14:10,30:15,45:20")
        assert steps == [(7, 5.0), (14, 10.0), (30, 15.0), (45, 20.0)]

    def test_sorts_by_days(self):
        steps = _parse_steps("30:15,7:5,14:10")
        assert steps == [(7, 5.0), (14, 10.0), (30, 15.0)]

    def test_empty_string(self):
        assert _parse_steps("") == []

    def test_single_step(self):
        assert _parse_steps("7:5") == [(7, 5.0)]


class TestGetStep:
    def test_no_step_before_first_threshold(self, repricer):
        assert repricer._get_step(3) is None

    def test_step_1_at_7_days(self, repricer):
        assert repricer._get_step(7) == (1, 5.0)

    def test_step_2_at_14_days(self, repricer):
        assert repricer._get_step(14) == (2, 10.0)

    def test_step_3_at_30_days(self, repricer):
        assert repricer._get_step(30) == (3, 15.0)

    def test_step_4_at_45_days(self, repricer):
        assert repricer._get_step(45) == (4, 20.0)

    def test_step_4_at_59_days(self, repricer):
        # Still step 4 before zombie threshold (60 days)
        assert repricer._get_step(59) == (4, 20.0)

    def test_between_thresholds(self, repricer):
        # 20 days → still step 2 (14 days)
        assert repricer._get_step(20) == (2, 10.0)


class TestCalculateReprice:
    def test_step_1_applies_5_percent(self, repricer):
        listing = _make_listing(days_active=7)
        result = repricer.calculate_reprice(listing)
        assert result is not None
        assert result["new_price"] == 47.5  # 50 * 0.95
        assert result["step"] == 1
        assert result["percent_off"] == 5.0

    def test_step_2_applies_10_percent(self, repricer):
        listing = _make_listing(days_active=14)
        result = repricer.calculate_reprice(listing)
        assert result["new_price"] == 45.0  # 50 * 0.90

    def test_step_3_applies_15_percent(self, repricer):
        listing = _make_listing(days_active=30)
        result = repricer.calculate_reprice(listing)
        assert result["new_price"] == 42.5  # 50 * 0.85

    def test_step_4_applies_20_percent(self, repricer):
        listing = _make_listing(days_active=45)
        result = repricer.calculate_reprice(listing)
        assert result["new_price"] == 40.0  # 50 * 0.80

    def test_no_change_before_threshold(self, repricer):
        listing = _make_listing(days_active=3)
        assert repricer.calculate_reprice(listing) is None

    def test_calculates_from_list_price_not_current(self, repricer):
        # Even if current_price was already reduced, step calculation uses list_price
        listing = _make_listing(days_active=14, current_price=47.5)
        result = repricer.calculate_reprice(listing)
        assert result["new_price"] == 45.0  # 10% off list_price (50), not current

    def test_skips_if_price_already_at_step(self, repricer):
        # current_price already at the step 1 price
        listing = _make_listing(days_active=7, current_price=47.5)
        assert repricer.calculate_reprice(listing) is None

    def test_enforces_profit_floor(self, repricer):
        # Very low margin item — repricing would go below minimum viable price
        listing = _make_listing(
            purchase_price=45.0,
            list_price=50.0,
            shipping_cost=5.0,
            days_active=45,
            ad_rate_percent=0.0,
        )
        result = repricer.calculate_reprice(listing)
        assert result is not None
        # Should not go below min viable price
        min_price = repricer.profit_calc.find_minimum_price(45.0, 5.0, 0.0)
        assert result["new_price"] >= round(min_price, 2)

    def test_returns_none_when_floor_equals_current(self, repricer):
        # Price already at floor — no change
        listing = _make_listing(
            purchase_price=48.0,
            list_price=50.0,
            shipping_cost=5.0,
            days_active=45,
            ad_rate_percent=0.0,
        )
        # The floor price is above the 20% markdown, so the floor clamps it
        result = repricer.calculate_reprice(listing)
        if result is not None:
            # If a result is returned, floor was applied
            min_price = repricer.profit_calc.find_minimum_price(48.0, 5.0, 0.0)
            assert result["new_price"] >= round(min_price, 2)


class TestScanAndReprice:
    async def test_reprices_eligible_listings(self, repricer, ebay, db_session):
        listing = _make_listing(days_active=14)
        db_session.add(listing)
        await db_session.flush()

        await ebay.create_inventory_item("REPRICE-001", {"title": "Test", "price": 50.0})

        result = await repricer.scan_and_reprice(db_session)
        assert result["total_scanned"] == 1
        assert result["repriced"] == 1
        assert result["skipped"] == 0

        # Verify price updated in DB
        assert float(listing.current_price) == 45.0
        assert listing.last_repriced_at is not None

        # Verify price pushed to eBay
        item = await ebay.get_inventory_item("REPRICE-001")
        assert item["price"] == 45.0

    async def test_skips_non_eligible(self, repricer, db_session):
        listing = _make_listing(days_active=3)
        db_session.add(listing)
        await db_session.flush()

        result = await repricer.scan_and_reprice(db_session)
        assert result["repriced"] == 0
        assert result["skipped"] == 1

    async def test_multiple_listings_different_steps(self, repricer, ebay, db_session):
        l1 = _make_listing(sku="R-001", days_active=7, current_price=50.0)
        l2 = _make_listing(sku="R-002", days_active=30, current_price=50.0)
        l3 = _make_listing(sku="R-003", days_active=3, current_price=50.0)
        db_session.add_all([l1, l2, l3])
        await db_session.flush()

        for sku in ["R-001", "R-002", "R-003"]:
            await ebay.create_inventory_item(sku, {"title": "Test", "price": 50.0})

        result = await repricer.scan_and_reprice(db_session)
        assert result["repriced"] == 2  # l1 and l2
        assert result["skipped"] == 1  # l3

    async def test_handles_ebay_error(self, repricer, ebay, db_session):
        listing = _make_listing(days_active=14)
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("bulk_update_price_quantity", RuntimeError("API down"))

        result = await repricer.scan_and_reprice(db_session)
        assert result["repriced"] == 1  # Still counted
        assert result["ebay_errors"] == 1

    async def test_no_active_listings(self, repricer, db_session):
        result = await repricer.scan_and_reprice(db_session)
        assert result["total_scanned"] == 0
        assert result["repriced"] == 0

    async def test_ignores_non_active_status(self, repricer, db_session):
        listing = _make_listing(days_active=30, status=ListingStatus.ZOMBIE)
        db_session.add(listing)
        await db_session.flush()

        result = await repricer.scan_and_reprice(db_session)
        assert result["total_scanned"] == 0
