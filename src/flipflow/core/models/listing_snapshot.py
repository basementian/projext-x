"""Listing snapshot model — time-series analytics for tracking performance."""

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class ListingSnapshot(Base, TimestampMixin):
    __tablename__ = "listing_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date)
    views: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    price_at_snapshot: Mapped[float] = mapped_column(Numeric(10, 2))
    status_at_snapshot: Mapped[str] = mapped_column(String(32))

    listing: Mapped["Listing"] = relationship(back_populates="snapshots")
