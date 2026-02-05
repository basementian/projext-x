"""SmartQueue — batch release listings during peak conversion windows.

Research: Sunday 8-10 PM ET is the highest conversion window on eBay.
Listing on Friday afternoon is "throwing impressions away."

The queue stores "ready" listings and releases them in batches
during the configurable surge window.
"""

import uuid
from datetime import datetime, timezone

import pytz
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, QueueStatus
from flipflow.core.models.listing import Listing
from flipflow.core.models.queue_entry import QueueEntry
from flipflow.core.protocols.ebay_gateway import EbayGateway


class SmartQueue:

    WEEKDAY_MAP = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6,
    }

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.batch_size = config.queue_batch_size
        self.surge_day = config.surge_window_day.lower()
        self.surge_start = config.surge_window_start_hour
        self.surge_end = config.surge_window_end_hour
        self.tz = pytz.timezone(config.surge_window_timezone)

    async def enqueue(
        self, db: AsyncSession, listing_id: int,
        priority: int = 0, window: str = "sunday_surge",
    ) -> QueueEntry:
        """Add a listing to the release queue."""
        listing = await db.get(Listing, listing_id)
        if listing is None:
            raise ValueError(f"Listing {listing_id} not found")

        entry = QueueEntry(
            listing_id=listing_id,
            priority=priority,
            scheduled_window=window,
            status=QueueStatus.PENDING,
        )
        listing.status = ListingStatus.QUEUED
        db.add(entry)
        await db.flush()
        return entry

    async def release_batch(self, db: AsyncSession, dry_run: bool = False) -> list[QueueEntry]:
        """Release the next batch of pending entries (highest priority first).

        In dry_run mode, returns what would be released without actually publishing.
        """
        stmt = (
            select(QueueEntry)
            .where(QueueEntry.status == QueueStatus.PENDING)
            .order_by(QueueEntry.priority.desc(), QueueEntry.created_at.asc())
            .limit(self.batch_size)
        )
        result = await db.execute(stmt)
        entries = list(result.scalars().all())

        if dry_run:
            return entries

        batch_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        released = []

        for entry in entries:
            listing = await db.get(Listing, entry.listing_id)
            if listing is None:
                entry.status = QueueStatus.FAILED
                entry.error_message = "Listing not found"
                continue

            try:
                # Create and publish on eBay
                offer = await self.ebay.create_offer({
                    "sku": listing.sku,
                    "marketplaceId": "EBAY_US",
                    "format": "FIXED_PRICE",
                    "pricingSummary": {
                        "price": {"value": str(listing.list_price), "currency": "USD"},
                    },
                })
                publish_result = await self.ebay.publish_offer(offer["offerId"])

                # Update listing
                listing.ebay_item_id = publish_result.get("listingId")
                listing.offer_id = offer["offerId"]
                listing.status = ListingStatus.ACTIVE
                listing.listed_at = now
                listing.days_active = 0

                # Update queue entry
                entry.status = QueueStatus.RELEASED
                entry.released_at = now
                entry.batch_id = batch_id
                released.append(entry)

            except Exception as e:
                entry.status = QueueStatus.FAILED
                entry.error_message = str(e)

        await db.flush()
        return released

    def is_surge_window_active(self, now: datetime | None = None) -> bool:
        """Check if current time is within the configured surge window."""
        if now is None:
            now = datetime.now(self.tz)
        elif now.tzinfo is None:
            now = self.tz.localize(now)
        else:
            now = now.astimezone(self.tz)

        target_day = self.WEEKDAY_MAP.get(self.surge_day, 6)
        return (
            now.weekday() == target_day
            and self.surge_start <= now.hour < self.surge_end
        )

    async def get_queue_status(self, db: AsyncSession) -> dict:
        """Get counts and summary of queue state."""
        today = datetime.now(timezone.utc).date()

        # Count by status
        stmt = select(QueueEntry.status, func.count()).group_by(QueueEntry.status)
        result = await db.execute(stmt)
        counts = dict(result.all())

        # Released today
        released_today_stmt = (
            select(func.count())
            .where(QueueEntry.status == QueueStatus.RELEASED)
            .where(func.date(QueueEntry.released_at) == today)
        )
        released_today_result = await db.execute(released_today_stmt)
        released_today = released_today_result.scalar() or 0

        return {
            "pending": counts.get(QueueStatus.PENDING, 0),
            "released_today": released_today,
            "failed": counts.get(QueueStatus.FAILED, 0),
            "total": sum(counts.values()),
            "surge_window_active": self.is_surge_window_active(),
        }
