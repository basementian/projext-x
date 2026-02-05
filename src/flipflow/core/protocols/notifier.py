"""Notifier protocol — abstraction for push notifications (future)."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class NotifierGateway(Protocol):
    """Abstraction for notifications. Stub for MVP, real impl later."""

    async def notify(self, event_type: str, payload: dict) -> None:
        """Send a notification for an event."""
        ...
