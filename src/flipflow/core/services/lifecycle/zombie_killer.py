"""Zombie Killer — detects stale listings that are invisible to Cassini.

A listing is a "zombie" if:
- Active for > threshold days (default 60)
- Total views < threshold (default 10)

Zombies have a "stale" Item ID. They are invisible to search.
The only cure is to generate a new Item ID (via the Resurrector).
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, ZombieAction
from flipflow.core.models.listing import Listing
from flipflow.core.models.zombie_record import ZombieRecord
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.core.schemas.analytics import ZombieReport, ZombieScanResult

logger = logging.getLogger(__name__)


class ZombieKiller:
    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.days_threshold = config.zombie_days_threshold
        self.views_threshold = config.zombie_views_threshold
        self.max_cycles = config.max_zombie_cycles

    async def scan(self, db: AsyncSession) -> ZombieScanResult:
        """Scan all active listings and detect zombies.

        Pulls traffic data from eBay Analytics API to get current view counts,
        then compares against thresholds.
        """
        # Get all active listings
        stmt = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        if not active_listings:
            return ZombieScanResult(
                total_scanned=0,
                zombies_found=0,
                purgatory_candidates=0,
                zombies=[],
            )

        # Fetch traffic data from eBay for listings that have item IDs
        listings_with_ids = [l for l in active_listings if l.ebay_item_id]
        traffic_data = {}
        if listings_with_ids:
            item_ids = [l.ebay_item_id for l in listings_with_ids]
            report = await self.ebay.get_traffic_report(item_ids, "LAST_90_DAYS", ["views"])
            for record in report.get("records", []):
                traffic_data[record["listingId"]] = record.get("views", 0)

        # Detect zombies
        zombies: list[ZombieReport] = []
        purgatory_count = 0

        for listing in active_listings:
            # Use eBay traffic data if available, else fall back to DB views
            views = listing.total_views
            if listing.ebay_item_id and listing.ebay_item_id in traffic_data:
                views = traffic_data[listing.ebay_item_id]
                # Sync views back to DB
                listing.total_views = views

            if listing.days_active >= self.days_threshold and views < self.views_threshold:
                should_purgatory = listing.zombie_cycle_count >= self.max_cycles
                if should_purgatory:
                    purgatory_count += 1

                zombies.append(
                    ZombieReport(
                        listing_id=listing.id,
                        sku=listing.sku,
                        title=listing.title,
                        ebay_item_id=listing.ebay_item_id,
                        days_active=listing.days_active,
                        total_views=views,
                        watchers=listing.watchers,
                        zombie_cycle_count=listing.zombie_cycle_count,
                        should_purgatory=should_purgatory,
                        current_price=listing.current_price or listing.list_price,
                    )
                )

        logger.info(
            "Zombie scan complete: %d scanned, %d zombies, %d purgatory candidates",
            len(active_listings),
            len(zombies),
            purgatory_count,
        )
        return ZombieScanResult(
            total_scanned=len(active_listings),
            zombies_found=len(zombies),
            purgatory_candidates=purgatory_count,
            zombies=zombies,
        )

    async def flag_zombie(self, db: AsyncSession, listing_id: int) -> ZombieRecord:
        """Mark a listing as zombie and create a tracking record."""
        listing = await db.get(Listing, listing_id)
        if listing is None:
            raise ValueError(f"Listing {listing_id} not found")

        listing.status = ListingStatus.ZOMBIE
        logger.info("Flagging listing %d (sku=%s) as zombie", listing_id, listing.sku)

        action = ZombieAction.FLAGGED
        if listing.zombie_cycle_count >= self.max_cycles:
            action = ZombieAction.PURGATORED
            listing.status = ListingStatus.PURGATORY

        record = ZombieRecord(
            listing_id=listing.id,
            detected_at=datetime.now(UTC),
            days_active_at_detection=listing.days_active,
            views_at_detection=listing.total_views,
            action_taken=action,
            cycle_number=listing.zombie_cycle_count + 1,
        )
        db.add(record)
        await db.flush()
        return record
