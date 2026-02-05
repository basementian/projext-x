"""Offer Sniper — converts watchers into buyers with instant offers.

Research: Buyers "watch" items to see if the price drops. Sending offers
immediately while they are interested is critical. Competitors wait days.

Flow: Poll for new watchers every hour → auto-send 10% off offer immediately.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway


class OfferSniper:
    """Detects new watchers and auto-sends discount offers."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.discount_percent = config.offer_discount_percent

    def calculate_offer_price(self, current_price: float) -> float:
        """Calculate the offer price after discount."""
        discount = self.discount_percent / 100
        return round(current_price * (1 - discount), 2)

    async def scan_and_snipe(self, db: AsyncSession) -> dict:
        """Scan all active listings for new watchers and send offers.

        Returns summary of offers sent.
        """
        stmt = select(Listing).where(
            Listing.status == ListingStatus.ACTIVE,
            Listing.ebay_item_id.isnot(None),
        )
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        offers_sent = 0
        errors = 0
        details = []

        for listing in active_listings:
            try:
                watchers = await self.ebay.get_watchers(listing.ebay_item_id)
                if not watchers:
                    continue

                price = float(listing.current_price or listing.list_price)
                offer_price = self.calculate_offer_price(price)

                for watcher in watchers:
                    buyer_id = watcher.get("buyerId")
                    if not buyer_id:
                        continue

                    # Skip if we already sent an offer recently
                    if listing.last_offer_sent_at:
                        hours_since = (
                            datetime.now(timezone.utc) - listing.last_offer_sent_at
                        ).total_seconds() / 3600
                        if hours_since < 24:
                            continue

                    try:
                        await self.ebay.send_offer_to_buyer(
                            listing.ebay_item_id,
                            buyer_id,
                            {
                                "price": offer_price,
                                "currency": "USD",
                                "message": f"Special offer: ${offer_price:.2f} ({self.discount_percent:.0f}% off)!",
                            },
                        )
                        offers_sent += 1
                        listing.last_offer_sent_at = datetime.now(timezone.utc)
                        details.append({
                            "listing_id": listing.id,
                            "sku": listing.sku,
                            "buyer_id": buyer_id,
                            "original_price": price,
                            "offer_price": offer_price,
                        })
                    except Exception as e:
                        errors += 1

            except Exception:
                errors += 1

        await db.flush()

        return {
            "listings_checked": len(active_listings),
            "offers_sent": offers_sent,
            "errors": errors,
            "details": details,
        }
