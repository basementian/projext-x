"""The Purgatory — liquidation pricing for chronic zombies.

Research: If an item survives the Zombie Killer 3 times (180+ days),
it's dead weight. It needs to be liquidated.

Logic: If zombie_cycle_count > 3:
  1. Auto-price at break-even
  2. Run 30% off sale
  3. If unsold in 7 days → suggest "Donate/Trash"
"""

from flipflow.core.config import FlipFlowConfig
from flipflow.core.constants import ListingStatus
from flipflow.core.models.listing import Listing
from flipflow.core.protocols.ebay_gateway import EbayGateway
from flipflow.core.services.gatekeeper.profit_floor import ProfitFloorCalc
from flipflow.core.schemas.profit import ProfitCalcRequest

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class Purgatory:
    """Liquidation pricing engine for chronic zombie listings."""

    def __init__(self, ebay: EbayGateway, config: FlipFlowConfig):
        self.ebay = ebay
        self.config = config
        self.sale_percent = config.purgatory_sale_percent
        self.profit_calc = ProfitFloorCalc(config)

    def calculate_break_even_price(self, listing: Listing) -> float:
        """Calculate the minimum price to break even (zero profit).

        Solving: 0 = sale - cost - shipping - (sale * fees)
        sale * (1 - fee_rate) = cost + shipping + per_order_fee
        sale = (cost + shipping + per_order_fee) / (1 - total_fee_rate)
        """
        total_fee_rate = (
            self.config.ebay_base_fee_rate
            + self.config.payment_processing_rate
        )
        denominator = 1 - total_fee_rate
        if denominator <= 0:
            return float("inf")

        cost = float(listing.purchase_price)
        shipping = float(listing.shipping_cost)
        return (cost + shipping + self.config.per_order_fee) / denominator

    def calculate_sale_price(self, listing: Listing) -> float:
        """Calculate the purgatory sale price (break-even with discount)."""
        break_even = self.calculate_break_even_price(listing)
        # The "sale price" is break-even — the discount is applied on top
        return round(break_even, 2)

    def calculate_markdown_price(self, listing: Listing) -> float:
        """Calculate the price after applying the sale discount.

        This is the actual displayed price: break_even * (1 - sale_percent/100)
        Note: This WILL lose money. That's the point of purgatory.
        """
        break_even = self.calculate_break_even_price(listing)
        discount = self.sale_percent / 100
        return round(break_even * (1 - discount), 2)

    def should_suggest_donate(self, listing: Listing, days_in_purgatory: int) -> bool:
        """After 7 days in purgatory at markdown price, suggest donation."""
        return (
            listing.status == ListingStatus.PURGATORY
            and days_in_purgatory >= 7
        )

    async def enter_purgatory(self, db: AsyncSession, listing_id: int) -> dict:
        """Move a listing into purgatory pricing.

        Sets price to break-even and applies markdown.
        """
        listing = await db.get(Listing, listing_id)
        if listing is None:
            return {"success": False, "error": "Listing not found"}

        break_even = self.calculate_break_even_price(listing)
        markdown = self.calculate_markdown_price(listing)

        listing.status = ListingStatus.PURGATORY
        listing.current_price = markdown

        # Update price on eBay
        if listing.sku:
            try:
                await self.ebay.bulk_update_price_quantity([{
                    "sku": listing.sku,
                    "price": markdown,
                }])
            except Exception as e:
                return {"success": False, "error": f"eBay update failed: {e}"}

        await db.flush()

        # Calculate how much we lose at markdown
        profit_result = self.profit_calc.calculate(ProfitCalcRequest(
            sale_price=markdown,
            purchase_price=float(listing.purchase_price),
            shipping_cost=float(listing.shipping_cost),
        ))

        return {
            "success": True,
            "listing_id": listing_id,
            "original_price": float(listing.list_price),
            "break_even_price": round(break_even, 2),
            "markdown_price": markdown,
            "sale_percent": self.sale_percent,
            "estimated_loss": round(abs(profit_result.net_profit), 2) if profit_result.net_profit < 0 else 0,
            "suggestion": "Will suggest Donate/Trash if unsold in 7 days",
        }

    async def scan_for_purgatory(self, db: AsyncSession) -> list[dict]:
        """Find all purgatory listings and check if they should be donated."""
        stmt = select(Listing).where(Listing.status == ListingStatus.PURGATORY)
        result = await db.execute(stmt)
        purgatory_listings = list(result.scalars().all())

        suggestions = []
        for listing in purgatory_listings:
            # Rough estimate: days_active is total, not purgatory-specific
            # In production, we'd track when they entered purgatory
            if listing.days_active > 7:
                suggestions.append({
                    "listing_id": listing.id,
                    "sku": listing.sku,
                    "title": listing.title,
                    "current_price": float(listing.current_price) if listing.current_price else 0,
                    "suggestion": "DONATE_OR_TRASH",
                })

        return suggestions
