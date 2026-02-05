"""Queue entry model — SmartQueue scheduled listing releases."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, TimestampMixin


class QueueEntry(Base, TimestampMixin):
    __tablename__ = "queue_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_window: Mapped[str] = mapped_column(String(32), default="sunday_surge")
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    batch_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    listing: Mapped["Listing"] = relationship(back_populates="queue_entries")
