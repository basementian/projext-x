"""Pydantic schemas for profit calculations."""

from pydantic import BaseModel, Field


class ProfitCalcRequest(BaseModel):
    """Input for profit calculation."""

    sale_price: float = Field(gt=0, description="Expected sale price")
    purchase_price: float = Field(ge=0, description="Cost to acquire the item")
    shipping_cost: float = Field(ge=0, default=0, description="Shipping cost")
    ad_rate_percent: float = Field(
        ge=0, default=0, description="Promoted listing ad rate (e.g. 1.5 for 1.5%)"
    )


class ProfitCalcResponse(BaseModel):
    """Output of profit calculation."""

    sale_price: float
    purchase_price: float
    shipping_cost: float

    # Fee breakdown
    ebay_fee_rate: float
    ebay_fee_amount: float
    ad_rate_percent: float
    ad_fee_amount: float
    payment_processing_amount: float
    per_order_fee: float
    total_fees: float

    # Result
    net_profit: float
    profit_margin_percent: float
    meets_floor: bool
    profit_floor: float

    # Advisory
    minimum_viable_price: float  # Lowest price to hit profit floor
