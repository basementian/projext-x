"""Store Pulse — forces eBay to re-index your entire store.

Research: Changing the "Handling Time" on all items forces eBay to
re-index your entire store to update delivery dates. This refreshes
your listings' position in search results.

Flow: Toggle Handling Time 1→2 days, wait 24h, toggle back. Monthly.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig

logger = logging.getLogger(__name__)
from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway


class StorePulse:
    """Monthly store re-indexing via handling time toggle."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.config = config

    async def toggle_handling_time(
        self, db: AsyncSession, target_days: int = 2,
    ) -> dict:
        """Toggle handling time on all active listings to force re-index.

        Args:
            db: Database session
            target_days: New handling time (toggle to this, then back later)

        Returns:
            dict with count of updated listings and any errors
        """
        stmt = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        if not active_listings:
            return {"updated": 0, "errors": 0, "message": "No active listings"}

        # Build bulk update
        updates = []
        for listing in active_listings:
            if listing.ebay_item_id:
                updates.append({
                    "sku": listing.sku,
                    "handling_days": target_days,
                })

        if not updates:
            return {"updated": 0, "errors": 0, "message": "No listings with eBay IDs"}

        try:
            result = await self.ebay.bulk_update_price_quantity(updates)
            success_count = sum(
                1 for r in result.get("responses", [])
                if r.get("status") == "SUCCESS"
            )
            error_count = len(updates) - success_count
            return {
                "updated": success_count,
                "errors": error_count,
                "total_active": len(active_listings),
                "target_handling_days": target_days,
            }
        except Exception as e:
            logger.error("Store pulse bulk update failed: %s", e)
            return {
                "updated": 0,
                "errors": len(updates),
                "error_message": str(e),
            }

    async def revert_handling_time(self, db: AsyncSession) -> dict:
        """Revert handling time back to 1 day (called 24h after toggle)."""
        return await self.toggle_handling_time(db, target_days=1)
