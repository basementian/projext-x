"""Scheduler protocol — abstraction over job scheduling backends."""

from collections.abc import Callable
from typing import Protocol, runtime_checkable


@runtime_checkable
class SchedulerGateway(Protocol):
    """Abstraction over job scheduling.

    Implementations:
    - APSchedulerImpl: local APScheduler with SQLAlchemy job store
    - Future: CeleryImpl for distributed processing
    """

    def add_job(
        self, job_id: str, func: Callable, trigger: str, **trigger_args,
    ) -> None:
        """Add a scheduled job."""
        ...

    def remove_job(self, job_id: str) -> bool:
        """Remove a job. Returns True if found and removed."""
        ...

    def pause_job(self, job_id: str) -> bool:
        """Pause a job. Returns True if found and paused."""
        ...

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job. Returns True if found and resumed."""
        ...

    def get_job_status(self, job_id: str) -> dict | None:
        """Get status of a specific job. Returns None if not found."""
        ...

    def get_all_jobs(self) -> list[dict]:
        """Get status of all registered jobs."""
        ...

    def start(self) -> None:
        """Start the scheduler."""
        ...

    def shutdown(self) -> None:
        """Shut down the scheduler."""
        ...
