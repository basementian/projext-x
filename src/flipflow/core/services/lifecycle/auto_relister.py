"""Auto Relister — proactive scheduled relisting to prevent zombie death.

Flipwise auto-relists every 1-3 months before listings go stale.
FlipFlow used to wait for zombie detection (60+ days, <10 views) then react.

Now: preventive relist on a configurable cadence for low-traffic items.
Uses existing Resurrector pipeline (withdraw → cooldown → new SKU → publish).
Does NOT increment zombie_cycle_count — this is preventive, not reactive.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, RelistAction
from flipflow.core.models.listing import Listing
from flipflow.core.models.zombie_record import ZombieRecord
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.core.services.lifecycle.resurrector import Resurrector

logger = logging.getLogger(__name__)


class AutoRelister:
    """Preventive relisting for low-traffic active listings."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.config = config
        self.cadence_days = config.relist_cadence_days
        self.views_threshold = config.relist_views_threshold
        self.resurrector = Resurrector(ebay, config)

    def _is_due_for_relist(self, listing: Listing) -> bool:
        """Check if a listing is due for preventive relist."""
        return (
            listing.status == ListingStatus.ACTIVE
            and listing.days_active >= self.cadence_days
            and listing.total_views < self.views_threshold
            and listing.offer_id is not None
        )

    async def scan_for_relists(self, db: AsyncSession) -> list[dict]:
        """Find listings due for preventive relist (dry run)."""
        stmt = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        candidates = []
        for listing in active_listings:
            if self._is_due_for_relist(listing):
                candidates.append({
                    "listing_id": listing.id,
                    "sku": listing.sku,
                    "title": listing.title,
                    "days_active": listing.days_active,
                    "total_views": listing.total_views,
                    "current_price": float(listing.current_price or listing.list_price),
                })

        return candidates

    async def auto_relist(self, db: AsyncSession) -> dict:
        """Execute preventive relists for all eligible listings."""
        stmt = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        relisted = []
        skipped = 0
        errors = 0

        for listing in active_listings:
            if not self._is_due_for_relist(listing):
                skipped += 1
                continue

            old_item_id = listing.ebay_item_id
            old_cycle = listing.zombie_cycle_count

            # Use resurrector for the withdraw → create → publish pipeline
            res = await self.resurrector.resurrect(db, listing.id)

            if not res.success:
                errors += 1
                continue

            # Restore zombie_cycle_count — preventive relist is NOT a zombie cycle
            listing.zombie_cycle_count = old_cycle

            # Track as preventive relist
            record = ZombieRecord(
                listing_id=listing.id,
                detected_at=datetime.now(UTC),
                days_active_at_detection=listing.days_active,
                views_at_detection=listing.total_views,
                action_taken=RelistAction.PREVENTIVE_RELIST,
                resurrected_at=datetime.now(UTC),
                old_item_id=old_item_id,
                new_item_id=res.new_item_id,
                cycle_number=0,
            )
            db.add(record)

            relisted.append({
                "listing_id": listing.id,
                "sku": listing.sku,
                "old_item_id": old_item_id,
                "new_item_id": res.new_item_id,
            })

        await db.flush()

        logger.info("Auto relister: %d scanned, %d relisted, %d skipped, %d errors",
                    len(active_listings), len(relisted), skipped, errors)
        return {
            "total_scanned": len(active_listings),
            "relisted": len(relisted),
            "skipped": skipped,
            "errors": errors,
            "details": relisted,
        }
