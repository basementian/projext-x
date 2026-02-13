"""Offer record model — tracks per-watcher offer history."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class OfferRecord(Base, TimestampMixin):
    __tablename__ = "offer_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    buyer_id: Mapped[str] = mapped_column(String(128), index=True)
    offer_price: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="sent")

    listing: Mapped["Listing"] = relationship(back_populates="offer_records")
