"""Pydantic schemas for title sanitization."""

from pydantic import BaseModel, Field


class TitleSanitizeRequest(BaseModel):
    """Input for title sanitization."""
    title: str = Field(max_length=200, description="Raw listing title")
    brand: str | None = Field(default=None, description="Brand name to front-load")
    model: str | None = Field(default=None, description="Model name to front-load")


class TitleSanitizeResponse(BaseModel):
    """Output of title sanitization."""
    original: str
    sanitized: str
    changes: list[str]  # Human-readable list of what changed
    length: int
    brand_model_in_front: bool
