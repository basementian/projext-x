"""Graduated Repricer — time-based markdown ladder for active listings.

Competitors like StreetPricer and MyListerHub reprice dynamically.
FlipFlow used to go straight from full price to purgatory fire sale.

Now: configurable steps drop the price gradually based on days_active.
Always calculated from list_price (original), never compounding.
Never drops below ProfitFloorCalc.find_minimum_price() — the profit floor is the hard stop.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.core.services.gatekeeper.profit_floor import ProfitFloorCalc


def _parse_steps(steps_str: str) -> list[tuple[int, float]]:
    """Parse 'days:percent,...' into sorted list of (days, percent) tuples."""
    steps = []
    for pair in steps_str.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        days_str, pct_str = pair.split(":", 1)
        steps.append((int(days_str), float(pct_str)))
    steps.sort(key=lambda x: x[0])
    return steps


class Repricer:
    """Time-based markdown ladder for active listings."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.config = config
        self.steps = _parse_steps(config.reprice_steps)
        self.profit_calc = ProfitFloorCalc(config)

    def _get_step(self, days_active: int) -> tuple[int, float] | None:
        """Return (step_number, discount_percent) for the given days_active.

        Returns None if no step applies yet.
        """
        matched = None
        for i, (days, pct) in enumerate(self.steps):
            if days_active >= days:
                matched = (i + 1, pct)
        return matched

    def calculate_reprice(self, listing: Listing) -> dict | None:
        """Calculate new price for a listing based on days_active.

        Returns dict with reprice details, or None if no change needed.
        Always calculates from list_price (original), not current_price.
        """
        step = self._get_step(listing.days_active)
        if step is None:
            return None

        step_num, pct = step
        list_price = float(listing.list_price)
        new_price = round(list_price * (1 - pct / 100), 2)

        # Enforce profit floor
        min_price = self.profit_calc.find_minimum_price(
            float(listing.purchase_price),
            float(listing.shipping_cost),
            float(listing.ad_rate_percent),
        )
        if new_price < min_price:
            new_price = round(min_price, 2)

        # Skip if price hasn't changed
        current = float(listing.current_price or listing.list_price)
        if abs(new_price - current) < 0.01:
            return None

        return {
            "listing_id": listing.id,
            "sku": listing.sku,
            "step": step_num,
            "percent_off": pct,
            "old_price": current,
            "new_price": new_price,
            "min_viable_price": round(min_price, 2),
            "reason": f"Step {step_num}: {pct}% off after {listing.days_active} days",
        }

    async def scan_and_reprice(self, db: AsyncSession) -> dict:
        """Scan all active listings and apply graduated markdowns.

        Pushes price changes to eBay in a single batch call.
        """
        stmt = select(Listing).where(Listing.status == ListingStatus.ACTIVE)
        result = await db.execute(stmt)
        active_listings = list(result.scalars().all())

        repriced = []
        skipped = 0
        ebay_updates = []

        for listing in active_listings:
            reprice = self.calculate_reprice(listing)
            if reprice is None:
                skipped += 1
                continue

            listing.current_price = reprice["new_price"]
            listing.last_repriced_at = datetime.now(timezone.utc)
            repriced.append(reprice)

            if listing.sku:
                ebay_updates.append({
                    "sku": listing.sku,
                    "price": reprice["new_price"],
                })

        # Batch push to eBay
        ebay_errors = 0
        if ebay_updates:
            try:
                await self.ebay.bulk_update_price_quantity(ebay_updates)
            except Exception:
                ebay_errors = len(ebay_updates)

        await db.flush()

        logger.info("Repricer scan: %d scanned, %d repriced, %d skipped, %d eBay errors",
                    len(active_listings), len(repriced), skipped, ebay_errors)
        return {
            "total_scanned": len(active_listings),
            "repriced": len(repriced),
            "skipped": skipped,
            "ebay_errors": ebay_errors,
            "details": repriced,
        }
