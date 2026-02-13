"""Resurrector — kills zombie listings and reincarnates them with fresh Item IDs.

Flow:
1. Fetch full listing data (backup)
2. Withdraw the eBay offer (ends listing)
3. Wait for cooldown (120s default, 0 in tests)
4. Rotate photos (swap main image)
5. Create new inventory item with resurrection SKU suffix
6. Create and publish new offer → fresh Item ID
7. Update local DB with new IDs, increment zombie_cycle_count
"""

import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, ZombieAction
from flipflow.core.models.listing import Listing
from flipflow.core.models.zombie_record import ZombieRecord
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.core.schemas.analytics import ResurrectionResult

logger = logging.getLogger(__name__)


class Resurrector:

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.cooldown_seconds = config.resurrection_delay_seconds

    async def resurrect(self, db: AsyncSession, listing_id: int) -> ResurrectionResult:
        """Execute full resurrection pipeline for a single listing."""
        listing = await db.get(Listing, listing_id)
        if listing is None:
            return ResurrectionResult(
                listing_id=listing_id, sku="", old_item_id=None, new_item_id=None,
                new_offer_id=None, cycle_number=0, success=False,
                error=f"Listing {listing_id} not found",
            )

        old_item_id = listing.ebay_item_id
        old_offer_id = listing.offer_id
        cycle = listing.zombie_cycle_count + 1
        new_sku = self._generate_resurrection_sku(listing.sku, cycle)
        logger.info("Resurrecting listing %d (sku=%s) cycle %d", listing_id, listing.sku, cycle)

        # Step 1: Withdraw the existing offer (ends the listing on eBay)
        if old_offer_id:
            try:
                await self.ebay.withdraw_offer(old_offer_id)
            except Exception as e:
                logger.error("Failed to withdraw offer for listing %d: %s", listing_id, e)
                return self._fail(listing, cycle, f"Failed to withdraw offer: {e}")

        # Step 2: Cooldown — eBay needs time to clear the "Active" flag
        if self.cooldown_seconds > 0:
            await asyncio.sleep(self.cooldown_seconds)

        # Step 3: Rotate photos
        photo_urls = listing.photo_urls
        rotated_photos = self._rotate_photos(photo_urls)

        # Step 4: Create new inventory item
        item_data = {
            "title": listing.title_sanitized or listing.title,
            "description": listing.description_mobile or listing.description,
            "brand": listing.brand,
            "model": listing.model,
            "category_id": listing.category_id,
            "condition_id": listing.condition_id,
            "photo_urls": rotated_photos,
            "price": float(listing.list_price),
        }
        try:
            await self.ebay.create_inventory_item(new_sku, item_data)
        except Exception as e:
            logger.error("Failed to create inventory item for listing %d: %s", listing_id, e)
            return self._fail(listing, cycle, f"Failed to create inventory item: {e}")

        # Step 5: Create and publish offer
        try:
            offer = await self.ebay.create_offer({
                "sku": new_sku,
                "marketplaceId": "EBAY_US",
                "format": "FIXED_PRICE",
                "pricingSummary": {
                    "price": {"value": str(listing.list_price), "currency": "USD"},
                },
            })
            offer_id = offer["offerId"]
            publish_result = await self.ebay.publish_offer(offer_id)
            new_item_id = publish_result.get("listingId")
        except Exception as e:
            return self._fail(listing, cycle, f"Failed to publish offer: {e}")

        # Step 6: Update local DB
        now = datetime.now(UTC)
        listing.sku = new_sku
        listing.ebay_item_id = new_item_id
        listing.offer_id = offer_id
        listing.status = ListingStatus.ACTIVE
        listing.zombie_cycle_count = cycle
        listing.days_active = 0
        listing.total_views = 0
        listing.watchers = 0
        listing.photo_urls = rotated_photos
        listing.main_photo_index = 0
        listing.listed_at = now

        # Create zombie record
        record = ZombieRecord(
            listing_id=listing.id,
            detected_at=now,
            days_active_at_detection=listing.days_active,
            views_at_detection=listing.total_views,
            action_taken=ZombieAction.RESURRECTED,
            resurrected_at=now,
            old_item_id=old_item_id,
            new_item_id=new_item_id,
            cycle_number=cycle,
        )
        db.add(record)
        await db.flush()

        return ResurrectionResult(
            listing_id=listing.id,
            sku=new_sku,
            old_item_id=old_item_id,
            new_item_id=new_item_id,
            new_offer_id=offer_id,
            cycle_number=cycle,
            success=True,
            resurrected_at=now,
        )

    def _rotate_photos(self, photo_urls: list[str]) -> list[str]:
        """Swap first and second photos to make the listing look fresh."""
        if len(photo_urls) < 2:
            return photo_urls
        rotated = list(photo_urls)
        rotated[0], rotated[1] = rotated[1], rotated[0]
        return rotated

    def _generate_resurrection_sku(self, original_sku: str, cycle: int) -> str:
        """Generate a new SKU with resurrection suffix.

        NIKE-AM90-001 → NIKE-AM90-001_R1 → NIKE-AM90-001_R2
        """
        # Strip any existing _R suffix
        base = original_sku.split("_R")[0]
        return f"{base}_R{cycle}"

    def _fail(self, listing: Listing, cycle: int, error: str) -> ResurrectionResult:
        return ResurrectionResult(
            listing_id=listing.id,
            sku=listing.sku,
            old_item_id=listing.ebay_item_id,
            new_item_id=None,
            new_offer_id=None,
            cycle_number=cycle,
            success=False,
            error=error,
        )
