"""Profit Floor Calculator — prevents listings with hidden fee losses."""

from flipflow.core.config import FlipFlowConfig
from flipflow.core.schemas.profit import ProfitCalcRequest, ProfitCalcResponse


class ProfitFloorCalc:
    """Calculates net profit after all eBay fees and ad costs.

    Fee formula:
        ebay_fee = sale_price * base_fee_rate (default 13%)
        ad_fee = sale_price * ad_rate_percent / 100
        payment_fee = sale_price * payment_processing_rate + per_order_fee
        net = sale_price - purchase_price - shipping - ebay_fee - ad_fee - payment_fee
    """

    def __init__(self, config: FlipFlowConfig):
        self.base_fee_rate = config.ebay_base_fee_rate
        self.payment_processing_rate = config.payment_processing_rate
        self.per_order_fee = config.per_order_fee
        self.profit_floor = config.min_profit_floor

    def calculate(self, request: ProfitCalcRequest) -> ProfitCalcResponse:
        """Calculate net profit with full fee breakdown."""
        sale = request.sale_price
        cost = request.purchase_price
        shipping = request.shipping_cost
        ad_rate = request.ad_rate_percent / 100  # Convert percentage to decimal

        ebay_fee = sale * self.base_fee_rate
        ad_fee = sale * ad_rate
        payment_fee = sale * self.payment_processing_rate + self.per_order_fee
        total_fees = ebay_fee + ad_fee + payment_fee

        net_profit = sale - cost - shipping - total_fees
        margin = (net_profit / sale * 100) if sale > 0 else 0

        min_price = self.find_minimum_price(
            cost,
            shipping,
            request.ad_rate_percent,
        )

        return ProfitCalcResponse(
            sale_price=round(sale, 2),
            purchase_price=round(cost, 2),
            shipping_cost=round(shipping, 2),
            ebay_fee_rate=self.base_fee_rate,
            ebay_fee_amount=round(ebay_fee, 2),
            ad_rate_percent=request.ad_rate_percent,
            ad_fee_amount=round(ad_fee, 2),
            payment_processing_amount=round(payment_fee, 2),
            per_order_fee=self.per_order_fee,
            total_fees=round(total_fees, 2),
            net_profit=round(net_profit, 2),
            profit_margin_percent=round(margin, 2),
            meets_floor=net_profit >= self.profit_floor,
            profit_floor=self.profit_floor,
            minimum_viable_price=round(min_price, 2),
        )

    def find_minimum_price(
        self, purchase_price: float, shipping: float, ad_rate_percent: float
    ) -> float:
        """Reverse-calculate: minimum list price to hit the profit floor.

        Solving for sale_price in:
        profit_floor = sale - cost - shipping - (sale * base_fee) - (sale * ad) - (sale * payment) - per_order
        profit_floor + cost + shipping + per_order = sale * (1 - base_fee - ad - payment)
        sale = (profit_floor + cost + shipping + per_order) / (1 - base_fee - ad - payment)
        """
        ad_rate = ad_rate_percent / 100
        fee_multiplier = 1 - self.base_fee_rate - ad_rate - self.payment_processing_rate

        if fee_multiplier <= 0:
            # Fees exceed 100% of sale price — impossible to profit
            return float("inf")

        numerator = self.profit_floor + purchase_price + shipping + self.per_order_fee
        return numerator / fee_multiplier
