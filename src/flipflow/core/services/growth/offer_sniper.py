"""Offer Sniper — converts watchers into buyers with tiered offers.

V2: Age-based discount tiers (not flat 10%), per-watcher cooldown (not per-listing),
and inbound offer handling (auto-accept/counter/reject).

Competitors like MyListerHub use tiered thresholds. FlipFlow now matches that.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus, OfferAction, OfferStatus
from flipflow.core.models.listing import Listing
from flipflow.core.models.offer_record import OfferRecord
from flipflow.core.protocols.ebay_gateway import EbayGateway

logger = logging.getLogger(__name__)


def _parse_tiers(tiers_str: str) -> list[tuple[int, float]]:
    """Parse 'days:percent,...' into sorted list of (days, percent) tuples."""
    tiers = []
    for pair in tiers_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        days_str, pct_str = pair.split(":", 1)
        tiers.append((int(days_str), float(pct_str)))
    tiers.sort(key=lambda x: x[0])
    return tiers


class OfferSniper:
    """Detects new watchers and auto-sends tiered discount offers.

    Also handles incoming offers with accept/counter/reject thresholds.
    """

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.tiers = _parse_tiers(config.offer_tiers)
        self.auto_accept_threshold = config.offer_auto_accept_threshold
        self.counter_threshold = config.offer_counter_threshold
        self.counter_percent = config.offer_counter_percent

    def get_discount_percent(self, days_active: int) -> float:
        """Get the discount percentage based on listing age."""
        matched_pct = self.tiers[0][1] if self.tiers else 10.0
        for days, pct in self.tiers:
            if days_active >= days:
                matched_pct = pct
        return matched_pct

    def calculate_offer_price(self, current_price: float, days_active: int = 0) -> float:
        """Calculate the offer price after age-based discount."""
        pct = self.get_discount_percent(days_active)
        return round(current_price * (1 - pct / 100), 2)

    async def _was_offer_sent_recently(
        self, db: AsyncSession, listing_id: int, buyer_id: str,
    ) -> bool:
        """Check if an offer was sent to this specific buyer in the last 24 hours."""
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        stmt = select(OfferRecord).where(
            and_(
                OfferRecord.listing_id == listing_id,
                OfferRecord.buyer_id == buyer_id,
                OfferRecord.sent_at >= cutoff,
            )
        )
        result = await db.execute(stmt)
        return result.scalars().first() is not None

    async def scan_and_snipe(self, db: AsyncSession) -> dict:
        """Scan all active listings for new watchers and send tiered offers.

        Cooldown is now per-watcher (via OfferRecord), not per-listing.
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
                discount_pct = self.get_discount_percent(listing.days_active)
                offer_price = self.calculate_offer_price(price, listing.days_active)

                for watcher in watchers:
                    buyer_id = watcher.get("buyerId")
                    if not buyer_id:
                        continue

                    # Per-watcher cooldown check
                    if await self._was_offer_sent_recently(db, listing.id, buyer_id):
                        continue

                    try:
                        await self.ebay.send_offer_to_buyer(
                            listing.ebay_item_id,
                            buyer_id,
                            {
                                "price": offer_price,
                                "currency": "USD",
                                "message": (
                                    f"Special offer: ${offer_price:.2f} ({discount_pct:.0f}% off)!"
                                ),
                            },
                        )
                        offers_sent += 1

                        # Record the offer
                        record = OfferRecord(
                            listing_id=listing.id,
                            buyer_id=buyer_id,
                            offer_price=offer_price,
                            discount_percent=discount_pct,
                            sent_at=datetime.now(UTC),
                            status=OfferStatus.SENT,
                        )
                        db.add(record)

                        details.append({
                            "listing_id": listing.id,
                            "sku": listing.sku,
                            "buyer_id": buyer_id,
                            "original_price": price,
                            "offer_price": offer_price,
                            "discount_percent": discount_pct,
                            "days_active": listing.days_active,
                        })
                    except Exception as e:
                        logger.error("Failed to send offer for listing %d to %s: %s",
                                     listing.id, buyer_id, e)
                        errors += 1

            except Exception as e:
                logger.error("Failed to get watchers for listing %d: %s", listing.id, e)
                errors += 1

        await db.flush()

        logger.info("Offer sniper: %d checked, %d offers sent, %d errors",
                    len(active_listings), offers_sent, errors)
        return {
            "listings_checked": len(active_listings),
            "offers_sent": offers_sent,
            "errors": errors,
            "details": details,
        }

    async def handle_incoming_offer(
        self, db: AsyncSession, listing_id: int, buyer_id: str,
        offer_id: str, offer_amount: float,
    ) -> dict:
        """Handle an incoming buyer offer with accept/counter/reject thresholds.

        ratio >= 0.90 → auto-accept
        ratio >= 0.75 → counter at 95% of current price
        ratio <  0.75 → reject
        """
        listing = await db.get(Listing, listing_id)
        if listing is None:
            return {"success": False, "error": "Listing not found"}

        current_price = float(listing.current_price or listing.list_price)
        if current_price <= 0:
            return {"success": False, "error": "Invalid listing price"}

        ratio = offer_amount / current_price

        if ratio >= self.auto_accept_threshold:
            action = OfferAction.ACCEPT
            counter_amount = None
        elif ratio >= self.counter_threshold:
            action = OfferAction.COUNTER
            counter_amount = round(current_price * self.counter_percent, 2)
        else:
            action = OfferAction.REJECT
            counter_amount = None

        try:
            await self.ebay.respond_to_offer(
                listing.ebay_item_id, offer_id, action, counter_amount,
            )
        except Exception as e:
            return {"success": False, "error": f"eBay API error: {e}"}

        # Record the interaction
        status = OfferStatus.ACCEPTED if action == OfferAction.ACCEPT else OfferStatus.SENT
        record = OfferRecord(
            listing_id=listing.id,
            buyer_id=buyer_id,
            offer_price=offer_amount,
            discount_percent=round((1 - ratio) * 100, 2),
            sent_at=datetime.now(UTC),
            status=status,
        )
        db.add(record)
        await db.flush()

        return {
            "success": True,
            "listing_id": listing_id,
            "action": action,
            "offer_amount": offer_amount,
            "current_price": current_price,
            "ratio": round(ratio, 4),
            "counter_amount": counter_amount,
        }
