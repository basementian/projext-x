"""Listing model — the core entity of FlipFlow."""

import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from flipflow.core.models.base import Base, SoftDeleteMixin, TimestampMixin


class Listing(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    ebay_item_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    sku: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(80))
    title_sanitized: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    description_mobile: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    condition_id: Mapped[str] = mapped_column(String(16), default="3000")  # Used

    # Pricing
    purchase_price: Mapped[float] = mapped_column(Numeric(10, 2))
    list_price: Mapped[float] = mapped_column(Numeric(10, 2))
    current_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    shipping_cost: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    ad_rate_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    # Status tracking
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    listed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    days_active: Mapped[int] = mapped_column(Integer, default=0)
    total_views: Mapped[int] = mapped_column(Integer, default=0)
    watchers: Mapped[int] = mapped_column(Integer, default=0)
    zombie_cycle_count: Mapped[int] = mapped_column(Integer, default=0)

    # STR data
    sell_through_rate: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    str_data_source: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Photo management (JSON array of URLs)
    photo_urls_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    main_photo_index: Mapped[int] = mapped_column(Integer, default=0)

    # eBay offer tracking
    offer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_offer_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Repricing tracking
    last_repriced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    snapshots: Mapped[list["ListingSnapshot"]] = relationship(back_populates="listing")
    zombie_records: Mapped[list["ZombieRecord"]] = relationship(back_populates="listing")
    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="listing")
    profit_records: Mapped[list["ProfitRecord"]] = relationship(back_populates="listing")
    queue_entries: Mapped[list["QueueEntry"]] = relationship(back_populates="listing")
    offer_records: Mapped[list["OfferRecord"]] = relationship(back_populates="listing")

    @property
    def photo_urls(self) -> list[str]:
        if not self.photo_urls_json:
            return []
        return json.loads(self.photo_urls_json)

    @photo_urls.setter
    def photo_urls(self, urls: list[str]):
        self.photo_urls_json = json.dumps(urls)
