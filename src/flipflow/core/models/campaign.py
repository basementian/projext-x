"""Campaign model — Promoted Listings tracking."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    ebay_campaign_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    campaign_type: Mapped[str] = mapped_column(String(32))
    ad_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="active")

    listing: Mapped["Listing"] = relationship(back_populates="campaigns")
