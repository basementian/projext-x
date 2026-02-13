"""Tests for Kickstarter — auto-promote new listings."""

from datetime import UTC, datetime, timedelta

import pytest

from flipflow.core.constants import CampaignStatus, CampaignType, ListingStatus
from flipflow.core.models.campaign import Campaign
from flipflow.core.models.listing import Listing
from flipflow.core.services.growth.kickstarter import Kickstarter
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient


@pytest.fixture
def ebay():
    return MockEbayClient(load_fixtures=False)


@pytest.fixture
def kickstarter(ebay, test_config):
    return Kickstarter(ebay, test_config)


def _make_listing(**kwargs):
    defaults = {
        "sku": "KICK-001",
        "title": "New Item",
        "purchase_price": 20.0,
        "list_price": 50.0,
        "shipping_cost": 5.0,
        "status": ListingStatus.ACTIVE,
        "ebay_item_id": "EBAY-K001",
    }
    defaults.update(kwargs)
    return Listing(**defaults)


class TestPromoteNewListing:
    async def test_creates_campaign(self, kickstarter, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await kickstarter.promote_new_listing(db_session, listing.id)
        assert result["success"] is True
        assert result["ad_rate"] == 1.5
        assert result["duration_days"] == 14
        assert result["ebay_campaign_id"] is not None

    async def test_sets_ad_rate_on_listing(self, kickstarter, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        await kickstarter.promote_new_listing(db_session, listing.id)
        assert float(listing.ad_rate_percent) == 1.5

    async def test_nonexistent_listing(self, kickstarter, db_session):
        result = await kickstarter.promote_new_listing(db_session, 9999)
        assert result["success"] is False
        assert "not found" in result["error"]

    async def test_inactive_listing_rejected(self, kickstarter, db_session):
        listing = _make_listing(status=ListingStatus.ENDED)
        db_session.add(listing)
        await db_session.flush()

        result = await kickstarter.promote_new_listing(db_session, listing.id)
        assert result["success"] is False
        assert "not active" in result["error"]

    async def test_duplicate_campaign_rejected(self, kickstarter, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # First campaign succeeds
        result1 = await kickstarter.promote_new_listing(db_session, listing.id)
        assert result1["success"] is True

        # Second should fail
        result2 = await kickstarter.promote_new_listing(db_session, listing.id)
        assert result2["success"] is False
        assert "already exists" in result2["error"]

    async def test_ebay_api_error(self, kickstarter, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        ebay.inject_failure("create_campaign", RuntimeError("eBay down"))

        result = await kickstarter.promote_new_listing(db_session, listing.id)
        assert result["success"] is False
        assert "eBay" in result["error"]

    async def test_campaign_ends_at_correct_time(self, kickstarter, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        result = await kickstarter.promote_new_listing(db_session, listing.id)
        ends_at = datetime.fromisoformat(result["ends_at"])
        # Should be roughly 14 days from now
        expected = datetime.now(UTC) + timedelta(days=14)
        delta = abs((ends_at - expected).total_seconds())
        assert delta < 60  # Within a minute


class TestCleanupExpired:
    async def test_ends_expired_campaigns(self, kickstarter, ebay, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        # Create an expired campaign
        past = datetime.now(UTC) - timedelta(days=1)
        campaign = Campaign(
            listing_id=listing.id,
            ebay_campaign_id="CAMP-expired",
            campaign_type=CampaignType.KICKSTARTER,
            ad_rate_percent=1.5,
            started_at=past - timedelta(days=14),
            ends_at=past,
            status=CampaignStatus.ACTIVE,
        )
        db_session.add(campaign)
        listing.ad_rate_percent = 1.5
        await db_session.flush()

        # Register campaign in mock
        ebay.campaigns["CAMP-expired"] = {"campaignId": "CAMP-expired", "status": "RUNNING"}

        result = await kickstarter.cleanup_expired(db_session)
        assert result["expired_found"] == 1
        assert result["ended"] == 1
        assert result["errors"] == 0
        assert campaign.status == CampaignStatus.ENDED
        assert float(listing.ad_rate_percent) == 0

    async def test_ignores_future_campaigns(self, kickstarter, db_session):
        listing = _make_listing()
        db_session.add(listing)
        await db_session.flush()

        future = datetime.now(UTC) + timedelta(days=7)
        campaign = Campaign(
            listing_id=listing.id,
            campaign_type=CampaignType.KICKSTARTER,
            ad_rate_percent=1.5,
            started_at=datetime.now(UTC),
            ends_at=future,
            status=CampaignStatus.ACTIVE,
        )
        db_session.add(campaign)
        await db_session.flush()

        result = await kickstarter.cleanup_expired(db_session)
        assert result["expired_found"] == 0
        assert result["ended"] == 0

    async def test_no_campaigns(self, kickstarter, db_session):
        result = await kickstarter.cleanup_expired(db_session)
        assert result["expired_found"] == 0
        assert result["ended"] == 0
