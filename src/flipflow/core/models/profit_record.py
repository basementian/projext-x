"""Profit record model — tracks profit calculations per sale."""

from sqlalchemy import Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class ProfitRecord(Base, TimestampMixin):
    __tablename__ = "profit_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    sale_price: Mapped[float] = mapped_column(Numeric(10, 2))
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2))
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2))
    ebay_fee_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    ad_fee_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    ebay_fee_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    ad_fee_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    net_profit: Mapped[float] = mapped_column(Numeric(10, 2))
    profit_margin_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    meets_floor: Mapped[bool] = mapped_column(Boolean)

    listing: Mapped["Listing"] = relationship(back_populates="profit_records")
