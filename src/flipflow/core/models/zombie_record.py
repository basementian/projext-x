"""Zombie record model — tracks zombie detection and resurrection history."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class ZombieRecord(Base, TimestampMixin):
    __tablename__ = "zombie_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    days_active_at_detection: Mapped[int] = mapped_column(Integer)
    views_at_detection: Mapped[int] = mapped_column(Integer)
    action_taken: Mapped[str] = mapped_column(String(32))
    resurrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    old_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_item_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cycle_number: Mapped[int] = mapped_column(Integer, default=1)

    listing: Mapped["Listing"] = relationship(back_populates="zombie_records")
