"""Photo Shuffler — rotates main photo to test click-through rate.

Research: The main photo might be boring. Rotating the 2nd or 3rd image
to the "Main" slot tests if a different angle gets the click.

Rule: If views == 0 after 14 days → swap PictureURL[0] with PictureURL[1].
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway


class PhotoShuffler:
    """Rotates listing photos when CTR is zero."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.days_threshold = config.photo_shuffle_days_no_views

    async def scan_and_shuffle(self, db: AsyncSession) -> dict:
        """Find listings with 0 views past threshold and rotate their photos.

        Returns summary of what was shuffled.
        """
        stmt = select(Listing).where(
            Listing.status == ListingStatus.ACTIVE,
            Listing.days_active >= self.days_threshold,
            Listing.total_views == 0,
        )
        result = await db.execute(stmt)
        candidates = list(result.scalars().all())

        shuffled = []
        skipped = []

        for listing in candidates:
            photos = listing.photo_urls
            if len(photos) < 2:
                skipped.append({
                    "listing_id": listing.id,
                    "sku": listing.sku,
                    "reason": "Only 1 photo, cannot shuffle",
                })
                continue

            # Rotate: move next photo to main slot
            new_photos = self._rotate_photos(photos)
            listing.photo_urls = new_photos
            listing.main_photo_index = 0

            # Update on eBay if we have an item ID
            if listing.sku:
                try:
                    await self.ebay.update_inventory_item(listing.sku, {
                        "photo_urls": new_photos,
                    })
                    shuffled.append({
                        "listing_id": listing.id,
                        "sku": listing.sku,
                        "old_main": photos[0],
                        "new_main": new_photos[0],
                    })
                except Exception as e:
                    skipped.append({
                        "listing_id": listing.id,
                        "sku": listing.sku,
                        "reason": f"eBay update failed: {e}",
                    })

        await db.flush()

        return {
            "candidates": len(candidates),
            "shuffled": len(shuffled),
            "skipped": len(skipped),
            "details": shuffled,
            "skip_details": skipped,
        }

    def _rotate_photos(self, photo_urls: list[str]) -> list[str]:
        """Rotate photos: move second photo to first position."""
        if len(photo_urls) < 2:
            return list(photo_urls)
        rotated = list(photo_urls)
        rotated[0], rotated[1] = rotated[1], rotated[0]
        return rotated

    def needs_shuffle(self, listing: Listing) -> bool:
        """Check if a listing qualifies for photo shuffling."""
        return (
            listing.status == ListingStatus.ACTIVE
            and listing.days_active >= self.days_threshold
            and listing.total_views == 0
            and len(listing.photo_urls) >= 2
        )
