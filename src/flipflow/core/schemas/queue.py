"""Pydantic schemas for SmartQueue."""

from datetime import datetime

from pydantic import BaseModel


class QueueEntryResponse(BaseModel):
    """Queue entry details."""
    id: int
    listing_id: int
    sku: str
    title: str
    priority: int
    scheduled_window: str
    status: str
    scheduled_at: datetime | None
    released_at: datetime | None
    error_message: str | None = None


class QueueStatusResponse(BaseModel):
    """Overall queue status."""
    pending: int
    released_today: int
    failed: int
    total: int
    surge_window_active: bool
    next_surge_window: str | None
    entries: list[QueueEntryResponse]
