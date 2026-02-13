"""Kickstarter Mode — auto-creates Promoted Listings campaigns for new items.

Research: Organic rank is dead for new items. You need a "sales history"
to rank. Ad spend buys that history. Auto-creates a Promoted Listings
Standard campaign at 1.5% CPS for all new listings, runs for 14 days.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import CampaignStatus, CampaignType, ListingStatus
from flipflow.core.models.campaign import Campaign
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway

logger = logging.getLogger(__name__)


class Kickstarter:
    """Auto-promotes new listings with Promoted Listings Standard."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.ad_rate = config.kickstarter_ad_rate
        self.duration_days = config.kickstarter_duration_days

    async def promote_new_listing(
        self, db: AsyncSession, listing_id: int,
    ) -> dict:
        """Create a Promoted Listings campaign for a newly listed item.

        Args:
            db: Database session
            listing_id: The listing to promote

        Returns:
            dict with campaign details
        """
        listing = await db.get(Listing, listing_id)
        if listing is None:
            return {"success": False, "error": "Listing not found"}

        if listing.status != ListingStatus.ACTIVE:
            return {"success": False, "error": f"Listing is {listing.status}, not active"}

        # Check for existing active campaign
        stmt = select(Campaign).where(
            Campaign.listing_id == listing_id,
            Campaign.status == CampaignStatus.ACTIVE,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return {"success": False, "error": "Active campaign already exists"}

        now = datetime.now(UTC)
        ends_at = now + timedelta(days=self.duration_days)

        try:
            ebay_result = await self.ebay.create_campaign({
                "campaignName": f"Kickstart-{listing.sku}",
                "adRate": self.ad_rate,
                "listingId": listing.ebay_item_id,
            })
            ebay_campaign_id = ebay_result.get("campaignId")
        except Exception as e:
            logger.error("Failed to create campaign for listing %d: %s", listing_id, e)
            return {"success": False, "error": f"eBay API error: {e}"}

        campaign = Campaign(
            listing_id=listing_id,
            ebay_campaign_id=ebay_campaign_id,
            campaign_type=CampaignType.KICKSTARTER,
            ad_rate_percent=self.ad_rate,
            started_at=now,
            ends_at=ends_at,
            status=CampaignStatus.ACTIVE,
        )
        db.add(campaign)

        listing.ad_rate_percent = self.ad_rate
        await db.flush()

        return {
            "success": True,
            "campaign_id": campaign.id,
            "ebay_campaign_id": ebay_campaign_id,
            "ad_rate": self.ad_rate,
            "duration_days": self.duration_days,
            "ends_at": ends_at.isoformat(),
        }

    async def cleanup_expired(self, db: AsyncSession) -> dict:
        """End all campaigns that have passed their expiration date.

        Should be run daily via scheduler.
        """
        now = datetime.now(UTC)
        stmt = select(Campaign).where(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.ends_at <= now,
        )
        result = await db.execute(stmt)
        expired = list(result.scalars().all())

        ended = 0
        errors = 0

        for campaign in expired:
            try:
                if campaign.ebay_campaign_id:
                    await self.ebay.end_campaign(campaign.ebay_campaign_id)
                campaign.status = CampaignStatus.ENDED

                # Reset ad rate on listing
                listing = await db.get(Listing, campaign.listing_id)
                if listing:
                    listing.ad_rate_percent = 0

                ended += 1
            except Exception:
                errors += 1

        await db.flush()
        logger.info("Kickstarter cleanup: %d expired, %d ended, %d errors",
                    len(expired), ended, errors)
        return {"expired_found": len(expired), "ended": ended, "errors": errors}
