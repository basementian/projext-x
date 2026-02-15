"""Pydantic schemas for analytics and zombie reports."""

from datetime import datetime

from pydantic import BaseModel


class ZombieReport(BaseModel):
    """Report for a single detected zombie listing."""

    listing_id: int
    sku: str
    title: str
    ebay_item_id: str | None
    days_active: int
    total_views: int
    watchers: int
    zombie_cycle_count: int
    should_purgatory: bool  # True if exceeded max cycles
    current_price: float | None


class ZombieScanResult(BaseModel):
    """Result of a full zombie scan."""

    total_scanned: int
    zombies_found: int
    purgatory_candidates: int
    zombies: list[ZombieReport]


class ResurrectionResult(BaseModel):
    """Result of a single listing resurrection."""

    listing_id: int
    sku: str
    old_item_id: str | None
    new_item_id: str | None
    new_offer_id: str | None
    cycle_number: int
    success: bool
    error: str | None = None
    resurrected_at: datetime | None = None
